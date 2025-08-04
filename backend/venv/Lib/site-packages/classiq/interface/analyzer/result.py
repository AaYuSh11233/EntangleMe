from typing import Annotated, Literal, Optional, Union

import pydantic
from pydantic import Field
from typing_extensions import Self

from classiq.interface.analyzer.analysis_params import MAX_FILE_LENGTH
from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.custom_pydantic_types import PydanticNonEmptyString
from classiq.interface.helpers.versioned_model import VersionedModel

Match = list[list[int]]


class GraphStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class GraphResult(VersionedModel):
    kind: Literal["graph"] = Field(default="graph")
    details: str


class RbResults(VersionedModel):
    mean_fidelity: float
    average_error: float
    A: float
    B: float
    success_probability: list[float]
    parameters_error: tuple[float, ...]


class DataID(pydantic.BaseModel):
    id: str


class QasmCode(pydantic.BaseModel):
    code: str = Field(..., max_length=MAX_FILE_LENGTH)


class AnalysisStatus(StrEnum):
    NONE = "none"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    ERROR = "error"


class BasisGates(StrEnum):
    CX = "cx"
    CY = "cy"
    CZ = "cz"
    U = "u"
    U2 = "u2"
    P = "p"


class HardwareComparisonInformation(pydantic.BaseModel):
    devices: list[str] = pydantic.Field(
        default=..., description="Device which is used for the transpilation."
    )
    providers: list[str] = pydantic.Field(
        default=..., description="Provider cloud of the device."
    )
    depth: list[pydantic.NonNegativeInt] = pydantic.Field(
        default=..., description="Circuit depth."
    )
    multi_qubit_gate_count: list[pydantic.NonNegativeInt] = pydantic.Field(
        default=..., description="Number of multi qubit gates."
    )
    total_gate_count: list[pydantic.NonNegativeInt] = pydantic.Field(
        default=..., description="Number of total gates."
    )

    @pydantic.model_validator(mode="after")
    def validate_equal_length(self) -> Self:
        values = self.model_dump()
        lengths = list(map(len, values.values()))
        if len(set(lengths)) != 1:
            raise ClassiqValueError("All lists should have the same length")
        return self


# TODO: copy the types for `devices` & `providers` from `HardwareComparisonInformation`
#   Once https://github.com/Classiq-Technologies/Cadmium/pull/10069 is resolved
class SingleHardwareInformation(pydantic.BaseModel):
    devices: str = pydantic.Field(
        default=..., description="Device which is used for the transpilation."
    )
    providers: str = pydantic.Field(
        default=..., description="Provider cloud of the device."
    )
    depth: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Circuit depth."
    )
    multi_qubit_gate_count: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of multi qubit gates."
    )
    total_gate_count: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of total gates."
    )


class HardwareComparisonData(VersionedModel):
    kind: Literal["hardware_comparison"] = Field(default="hardware_comparison")
    data: list[SingleHardwareInformation]


HardwareComparisonGraphType = Annotated[
    Union[HardwareComparisonData, GraphResult], Field(discriminator="kind")
]

_HARDWARE_COMPARISON_TABLE_COLUMNS_NAMES: dict[str, str] = {
    s.upper(): s.capitalize() for s in SingleHardwareInformation.model_fields
}


class HardwareComparisonDataColumns(pydantic.BaseModel):
    columns: dict[str, str] = _HARDWARE_COMPARISON_TABLE_COLUMNS_NAMES


class AvailableHardware(pydantic.BaseModel):
    ibm_quantum: Optional[dict[PydanticNonEmptyString, bool]] = pydantic.Field(
        default=None,
        description="available IBM Quantum devices with boolean indicates if a given device has enough qubits.",
    )
    azure_quantum: Optional[dict[PydanticNonEmptyString, bool]] = pydantic.Field(
        default=None,
        description="available Azure Quantum devices with boolean indicates if a given device has enough qubits.",
    )
    amazon_braket: Optional[dict[PydanticNonEmptyString, bool]] = pydantic.Field(
        default=None,
        description="available Amazon Braket devices with boolean indicates if a given device has enough qubits.",
    )


class DevicesResult(VersionedModel):
    devices: AvailableHardware
    status: GraphStatus


class QuantumCircuitProperties(pydantic.BaseModel):
    depth: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Circuit depth"
    )
    auxiliary_qubits: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of Auxiliary qubits"
    )
    classical_bits: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of classical bits"
    )
    gates_count: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Total number of gates in the circuit"
    )
    multi_qubit_gates_count: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of multi-qubit gates in circuit"
    )
    non_entangled_subcircuits_count: pydantic.NonNegativeInt = pydantic.Field(
        default=..., description="Number of non-entangled sub-circuit "
    )


class NativeQuantumCircuitProperties(QuantumCircuitProperties):
    native_gates: set[BasisGates] = pydantic.Field(
        default=..., description="Native gates used for decomposition"
    )


class Circuit(pydantic.BaseModel):
    closed_circuit_qasm: str


class Analysis(VersionedModel):
    input_properties: QuantumCircuitProperties = pydantic.Field(
        default=..., description="Input circuit properties"
    )
    native_properties: NativeQuantumCircuitProperties = pydantic.Field(
        default=..., description="Transpiled circuit properties"
    )
