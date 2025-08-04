import functools
import operator
from collections import defaultdict
from collections.abc import Iterator, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Optional,
    Union,
)

import pandas as pd
import pydantic
from pydantic import BaseModel
from typing_extensions import Self, TypeAlias

from classiq.interface.exceptions import (
    ClassiqError,
    ClassiqInternalError,
    ClassiqValueError,
)
from classiq.interface.executor.quantum_code import OutputQubitsMap, Qubits
from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.complex_type import Complex
from classiq.interface.generator.functions.classical_type import QmodPyObject
from classiq.interface.helpers.custom_pydantic_types import PydanticNonNegIntTuple
from classiq.interface.helpers.datastructures import get_sdk_compatible_python_object
from classiq.interface.helpers.versioned_model import VersionedModel
from classiq.interface.model.quantum_type import RegisterQuantumTypeDict

_ILLEGAL_QUBIT_ERROR_MSG: str = "Illegal qubit index requested"
_REPEATED_QUBIT_ERROR_MSG: str = "Requested a qubit more than once"
_UNAVAILABLE_OUTPUT_ERROR_MSG: str = "Requested output doesn't exist in the circuit"

State: TypeAlias = str
Name: TypeAlias = str
RegisterValue: TypeAlias = Union[float, int, list, dict]
MeasuredShots: TypeAlias = pydantic.NonNegativeInt
ParsedState: TypeAlias = Mapping[Name, RegisterValue]
ParsedStates: TypeAlias = Mapping[State, ParsedState]
Counts: TypeAlias = dict[State, MeasuredShots]
StateVector: TypeAlias = Optional[dict[str, Complex]]

BITSTRING = "bitstring"
PROBABILITY = "probability"
AMPLITUDE = "amplitude"
COUNT = "count"

if TYPE_CHECKING:
    DotAccessParsedState = Mapping[Name, Any]
else:
    DotAccessParsedState = ParsedState


class SampledState(BaseModel):
    state: DotAccessParsedState
    shots: MeasuredShots

    def __repr__(self) -> str:
        return f"{self.state}: {self.shots}"

    @pydantic.field_validator("state", mode="after")
    @classmethod
    def _make_state_sdk_compatible(cls, state: ParsedState) -> DotAccessParsedState:
        return {
            name: get_sdk_compatible_python_object(value)
            for name, value in state.items()
        }


ParsedCounts: TypeAlias = list[SampledState]


class SimulatedState(BaseModel):
    state: ParsedState
    bitstring: State
    amplitude: Complex

    def __getitem__(self, item: Name) -> RegisterValue:
        return self.state[item]


SimulatedState.model_rebuild()
ParsedStateVector: TypeAlias = list[SimulatedState]


class VaRResult(BaseModel):
    var: Optional[float] = None
    alpha: Optional[float] = None


class GroverSimulationResults(VersionedModel):
    result: dict[str, Any]


def _validate_qubit_indices(counts: Counts, indices: tuple[int, ...]) -> None:
    if not indices:
        raise ClassiqError(_ILLEGAL_QUBIT_ERROR_MSG)

    if max(indices) >= len(list(counts.keys())[0]):
        raise ClassiqError(_ILLEGAL_QUBIT_ERROR_MSG)

    if len(set(indices)) < len(indices):
        raise ClassiqError(_REPEATED_QUBIT_ERROR_MSG)


def _slice_str(s: str, indices: tuple[int, ...]) -> str:
    return "".join(s[i] for i in indices)


def flip_counts_qubit_order(counts: Counts) -> Counts:
    return {key[::-1]: value for key, value in counts.items()}


def get_sampled_state(
    parsed_counts: ParsedCounts, state: ParsedState
) -> Optional[SampledState]:
    for sampled_state in parsed_counts:
        if sampled_state.state == state:
            return sampled_state
    return None


def reduce_parsed_states(
    parsed_states: ParsedStates, outputs: tuple[Name, ...]
) -> ParsedStates:
    return {
        state: {
            output: value for output, value in parsed_state.items() if output in outputs
        }
        for state, parsed_state in parsed_states.items()
    }


def get_parsed_counts(counts: Counts, parsed_states: ParsedStates) -> ParsedCounts:
    parsed_counts: ParsedCounts = []
    for bitstring, count in counts.items():
        parsed_state = parsed_states[bitstring]
        if sampled_state := get_sampled_state(parsed_counts, parsed_state):
            sampled_state.shots += count
        else:
            parsed_counts.append(SampledState(state=parsed_state, shots=count))
    return sorted(parsed_counts, key=lambda k: k.shots, reverse=True)


def prepare_parsed_state_vector(
    state_vector: StateVector, parsed_state_vector_states: ParsedStates
) -> Optional[ParsedStateVector]:
    if not state_vector:
        return None

    parsed_state_vector = [
        SimulatedState(
            state=parsed_state_vector_states[bitstring],
            bitstring=bitstring,
            amplitude=complex(amplitude_str),
        )
        for bitstring, amplitude_str in state_vector.items()
    ]
    return sorted(parsed_state_vector, key=lambda k: abs(k.amplitude), reverse=True)


def _flatten_columns(df: pd.DataFrame, columns_to_flatten: list[str]) -> pd.DataFrame:
    if len(df.columns) == 0:
        return df

    flattened_data = {}

    for col in columns_to_flatten:
        if col not in df.columns:
            continue

        flat_df = pd.json_normalize(df[col]).add_prefix(f"{col}.")
        flat_df.index = df.index
        flattened_data[col] = flat_df

    new_df_columns = []
    dfs_to_concat = []

    for col_name in df.columns:
        if col_name in flattened_data:
            new_df_columns.extend(flattened_data[col_name].columns)
            dfs_to_concat.append(flattened_data[col_name])
        elif col_name not in columns_to_flatten:
            new_df_columns.append(col_name)
            dfs_to_concat.append(df[[col_name]])

    final_df = pd.concat(dfs_to_concat, axis=1)
    valid_final_columns = [c for c in new_df_columns if c in final_df.columns]
    return final_df[valid_final_columns]


class ExecutionDetails(BaseModel, QmodPyObject):
    vendor_format_result: dict[str, Any] = pydantic.Field(
        ..., description="Result in proprietary vendor format"
    )
    counts: Counts = pydantic.Field(
        default_factory=dict, description="Number of counts per state"
    )
    counts_lsb_right: bool = pydantic.Field(
        True,
        description="Is the qubit order of counts field such that the LSB is right?",
    )
    probabilities: dict[State, pydantic.NonNegativeFloat] = pydantic.Field(
        default_factory=dict, description="Probabilities of each state"
    )
    parsed_states: ParsedStates = pydantic.Field(
        default_factory=dict,
        description="A mapping between the raw states of counts (bitstrings) to their parsed states (registers' values)",
    )
    histogram: Optional[dict[State, pydantic.NonNegativeFloat]] = pydantic.Field(
        None,
        description="Histogram of probability per state (an alternative to counts)",
    )
    output_qubits_map: OutputQubitsMap = pydantic.Field(
        default_factory=dict,
        description="The map of outputs (measured registers) to their qubits in the circuit.",
    )
    state_vector: StateVector = pydantic.Field(
        default=None,
        description="The state vector when executed on a simulator, with LSB right qubit order",
    )
    parsed_state_vector_states: Optional[ParsedStates] = pydantic.Field(
        default=None,
        description="A mapping between the raw states of the state vector (bitstrings) to their parsed states (registers' values)",
    )
    physical_qubits_map: Optional[OutputQubitsMap] = pydantic.Field(
        default=None,
        description="The map of all registers (also non measured) to their qubits in the circuit. Used for state_vector which represent also the non-measured qubits.",
    )
    num_shots: Optional[pydantic.NonNegativeInt] = pydantic.Field(
        default=None, description="The total number of shots the circuit was executed"
    )

    output_type_map: RegisterQuantumTypeDict = pydantic.Field(default_factory=dict)

    @pydantic.field_validator("counts", mode="after")
    @classmethod
    def _clean_spaces_from_counts_keys(cls, v: Counts) -> Counts:
        if not v or " " not in list(v.keys())[0]:
            return v
        return {state.replace(" ", ""): v[state] for state in v}

    @pydantic.model_validator(mode="after")
    def _validate_num_shots(self) -> Self:
        if isinstance(self, ExecutionDetails):
            if self.num_shots is not None:
                return self
            counts = self.counts
            if not counts:
                return self
            self.num_shots = sum(shots for _, shots in counts.items())
        return self

    @property
    def parsed_counts(self) -> ParsedCounts:
        return get_parsed_counts(self.counts, self.parsed_states)

    @property
    def parsed_state_vector(self) -> Optional[ParsedStateVector]:
        if TYPE_CHECKING:
            assert self.parsed_state_vector_states is not None
        return prepare_parsed_state_vector(
            self.state_vector, self.parsed_state_vector_states
        )

    def flip_execution_counts_bitstring(self) -> None:
        """Backends should return result count bitstring in right to left form"""
        self.counts = flip_counts_qubit_order(self.counts)
        self.counts_lsb_right = not self.counts_lsb_right

    def counts_by_qubit_order(self, lsb_right: bool) -> Counts:
        if self.counts_lsb_right != lsb_right:
            return flip_counts_qubit_order(self.counts)
        else:
            return self.counts

    def counts_of_qubits(self, *qubits: int) -> Counts:
        _validate_qubit_indices(self.counts, qubits)

        reduced_counts: DefaultDict[State, int] = defaultdict(int)
        for state_str, state_count in self.counts_by_qubit_order(
            lsb_right=False
        ).items():
            reduced_counts[_slice_str(state_str, qubits)] += state_count

        return dict(reduced_counts)

    def counts_of_output(self, output_name: Name) -> Counts:
        if output_name not in self.output_qubits_map:
            raise ClassiqError(_UNAVAILABLE_OUTPUT_ERROR_MSG)

        return self.counts_of_qubits(*self.output_qubits_map[output_name])

    def counts_of_multiple_outputs(
        self, output_names: tuple[Name, ...]
    ) -> dict[tuple[State, ...], pydantic.NonNegativeInt]:
        if any(name not in self.output_qubits_map for name in output_names):
            raise ClassiqError(_UNAVAILABLE_OUTPUT_ERROR_MSG)

        output_regs: tuple[Qubits, ...] = tuple(
            self.output_qubits_map[name] for name in output_names
        )
        reduced_counts: DefaultDict[tuple[State, ...], int] = defaultdict(int)
        for state_str, state_count in self.counts_by_qubit_order(
            lsb_right=False
        ).items():
            reduced_strs = tuple(_slice_str(state_str, reg) for reg in output_regs)
            reduced_counts[reduced_strs] += state_count
        return dict(reduced_counts)

    def parsed_counts_of_outputs(
        self, output_names: Union[Name, tuple[Name, ...]]
    ) -> ParsedCounts:
        if isinstance(output_names, Name):
            output_names = (output_names,)
        if any(name not in self.output_qubits_map for name in output_names):
            raise ClassiqError(_UNAVAILABLE_OUTPUT_ERROR_MSG)

        reduced_parsed_states = reduce_parsed_states(self.parsed_states, output_names)
        return get_parsed_counts(self.counts, reduced_parsed_states)

    def register_output_from_qubits(self, qubits: tuple[int, ...]) -> dict[float, int]:
        register_output: dict[float, int] = {}
        value_from_str_bin = functools.partial(
            self._get_register_value_from_binary_string_results, register_qubits=qubits
        )
        for results_binary_key, counts in self.counts_by_qubit_order(
            lsb_right=False
        ).items():
            value = value_from_str_bin(binary_string=results_binary_key)
            if TYPE_CHECKING:
                assert isinstance(value, float)
            register_output[value] = register_output.get(value, 0) + counts

        return register_output

    @staticmethod
    def _get_register_value_from_binary_string_results(
        binary_string: str, register_qubits: list[int]
    ) -> RegisterValue:
        register_binary_string = "".join(
            operator.itemgetter(*register_qubits)(binary_string)
        )[::-1]
        return number_utils.binary_to_float_or_int(bin_rep=register_binary_string)

    def _counts_df(self) -> pd.DataFrame:
        data: dict[str, Any] = defaultdict(list)

        for bitstring, count in self.counts.items():
            data[BITSTRING].append(bitstring)
            data[COUNT].append(count)
            if self.probabilities:
                data[PROBABILITY].append(self.probabilities[bitstring])
            elif self.num_shots:
                data[PROBABILITY].append(count / self.num_shots)

            for name, value in self.parsed_states[bitstring].items():
                data[name].append(value)

        final_columns = [COUNT, PROBABILITY, BITSTRING]
        columns = [
            col for col in data.keys() if col not in final_columns
        ] + final_columns

        return pd.DataFrame(data, columns=columns)

    def _state_vector_df(self) -> pd.DataFrame:
        data: dict[str, Any] = defaultdict(list)

        if not self.state_vector:
            raise ClassiqInternalError("No state vector")
        if not self.parsed_state_vector_states:
            raise ClassiqInternalError("No parsed state vector states")

        for bitstring, amplitude in self.state_vector.items():
            data[BITSTRING].append(bitstring)
            data[AMPLITUDE].append(amplitude)
            data[PROBABILITY].append(abs(amplitude) ** 2)
            for name, value in self.parsed_state_vector_states[bitstring].items():
                data[name].append(value)

        final_columns = [AMPLITUDE, PROBABILITY, BITSTRING]
        columns = [
            col for col in data.keys() if col not in final_columns
        ] + final_columns

        return pd.DataFrame(data, columns=columns)

    @functools.cached_property
    def dataframe(self) -> pd.DataFrame:
        reserved_words = frozenset([BITSTRING, PROBABILITY, COUNT, AMPLITUDE])
        _invalid_output_names = reserved_words.intersection(
            self.output_qubits_map.keys()
        )
        if _invalid_output_names:
            raise ClassiqValueError(f"Invalid output names: {_invalid_output_names}")

        if self.state_vector:
            df = self._state_vector_df()
        else:
            df = self._counts_df()

        df.sort_values(
            by=[AMPLITUDE if self.state_vector else COUNT, BITSTRING],
            inplace=True,
            ascending=[False, True],
            ignore_index=True,
        )

        outputs_to_flatten = [
            output
            for output, type in self.output_type_map.items()
            if type.quantum_types.kind == "struct_instance"
        ]
        df = _flatten_columns(df, outputs_to_flatten)
        return df


class MultipleExecutionDetails(VersionedModel):
    details: list[ExecutionDetails]

    def __getitem__(self, index: int) -> ExecutionDetails:
        return self.details[index]


class EstimationMetadata(BaseModel, extra="allow"):
    shots: Optional[pydantic.NonNegativeInt] = None
    remapped_qubits: bool = False
    input_qubit_map: Optional[list[PydanticNonNegIntTuple]] = None


class EstimationResult(BaseModel, QmodPyObject):
    value: Complex = pydantic.Field(..., description="Estimation for the operator")
    metadata: EstimationMetadata = pydantic.Field(
        ..., description="Metadata for the estimation"
    )


class EstimationResults(VersionedModel):
    results: list[EstimationResult]

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[EstimationResult]:  # type: ignore[override]
        # TODO This is a bug waiting to happen. We change the meaning of
        # __iter__ in a derived class.
        return iter(self.results)

    def __getitem__(self, index: int) -> EstimationResult:
        return self.results[index]
