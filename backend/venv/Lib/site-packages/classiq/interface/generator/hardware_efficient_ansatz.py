import itertools
from typing import TYPE_CHECKING, Optional, Union

import pydantic
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator import function_params
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
)
from classiq.interface.generator.transpiler_basis_gates import (
    SINGLE_QUBIT_GATES,
    TWO_QUBIT_GATES,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticNonNegIntTuple

ConnectivityMap = list[PydanticNonNegIntTuple]


class SupportedConnectivityMaps(StrEnum):
    FULL = "full"
    LINEAR = "linear"
    CIRCULAR = "circular"
    PAIRWISE = "pairwise"


ConnectivityMapType = Union[ConnectivityMap, SupportedConnectivityMaps, None]

_NUM_QUBITS_NOT_PROVIDED_ERROR = (
    "Either num_qubits or connectivity_map in the form of a list must be provided"
)


class HardwareEfficientAnsatz(function_params.FunctionParams):
    connectivity_map: ConnectivityMapType = pydantic.Field(
        default=None,
        description="Hardware's connectivity map, in the form [ [x0, x1], [x1, x2],...]. "
        "If none specified - use connectivity map from the model hardware settings. "
        "If none specified as well, all qubit pairs will be connected.",
    )
    num_qubits: pydantic.PositiveInt = pydantic.Field(
        default=None,
        description="Number of qubits in the ansatz.",
        validate_default=True,
    )
    reps: pydantic.PositiveInt = pydantic.Field(
        default=1, description="Number of layers in the Ansatz"
    )

    one_qubit_gates: Union[str, list[str]] = pydantic.Field(
        default=["x", "ry"],
        description='List of gates for the one qubit gates layer, e.g. ["x", "ry"]',
    )
    two_qubit_gates: Union[str, list[str]] = pydantic.Field(
        default=["cx"],
        description='List of gates for the two qubit gates entangling layer, e.g. ["cx", "cry"]',
    )
    parameter_prefix: str = pydantic.Field(
        default="hea_param_",
        description="Prefix for the generated parameters",
    )

    @pydantic.field_validator("num_qubits", mode="before")
    @classmethod
    def validate_num_qubits(
        cls, num_qubits: Optional[pydantic.PositiveInt], info: ValidationInfo
    ) -> pydantic.PositiveInt:
        connectivity_map = info.data.get("connectivity_map")
        conn_map_is_not_list = (
            isinstance(connectivity_map, SupportedConnectivityMaps)
            or connectivity_map is None
        )

        if num_qubits is None and conn_map_is_not_list:
            raise ClassiqValueError(_NUM_QUBITS_NOT_PROVIDED_ERROR)
        if num_qubits is None:
            if conn_map_is_not_list:
                raise ValueError(_NUM_QUBITS_NOT_PROVIDED_ERROR)

            if TYPE_CHECKING:
                assert connectivity_map is not None

            return len(set(itertools.chain.from_iterable(connectivity_map)))

        if conn_map_is_not_list:
            return num_qubits

        if TYPE_CHECKING:
            assert connectivity_map is not None

        invalid_qubits = {
            qubit
            for qubit in itertools.chain.from_iterable(connectivity_map)
            if qubit >= num_qubits
        }
        if invalid_qubits:
            raise ClassiqValueError(
                f"Invalid qubits: {invalid_qubits} "
                f"out of range specified by num_qubits: [0, {num_qubits - 1}]"
            )
        return num_qubits

    @pydantic.field_validator("one_qubit_gates")
    @classmethod
    def validate_one_qubit_gates(
        cls, one_qubit_gates: Union[str, list[str]]
    ) -> Union[str, list[str]]:
        one_qubit_gates_list = (
            [one_qubit_gates] if isinstance(one_qubit_gates, str) else one_qubit_gates
        )
        for one_qubit_gate in one_qubit_gates_list:
            if one_qubit_gate not in SINGLE_QUBIT_GATES:
                raise ClassiqValueError(f"Invalid one qubit gate: {one_qubit_gate}")
        return one_qubit_gates

    @pydantic.field_validator("two_qubit_gates")
    @classmethod
    def validate_two_qubit_gates(
        cls, two_qubit_gates: Union[str, list[str]]
    ) -> Union[str, list[str]]:
        two_qubit_gates_list = (
            [two_qubit_gates] if isinstance(two_qubit_gates, str) else two_qubit_gates
        )
        for two_qubit_gate in two_qubit_gates_list:
            if two_qubit_gate not in TWO_QUBIT_GATES:
                raise ClassiqValueError(f"Invalid two qubit gate: {two_qubit_gate}")
        return two_qubit_gates

    def _create_ios(self) -> None:
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterUserInput(
                name=DEFAULT_INPUT_NAME, size=self.num_qubits
            )
        }
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(
                name=DEFAULT_OUTPUT_NAME, size=self.num_qubits
            )
        }
