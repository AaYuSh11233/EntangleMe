from enum import IntEnum
from typing import Optional, Union

import pydantic

from classiq.interface.generator.generated_circuit_data import GeneratedFunction
from classiq.interface.generator.hardware.hardware_data import SynthesisHardwareData
from classiq.interface.helpers.versioned_model import VersionedModel
from classiq.interface.ide.visual_model import CircuitMetrics

GateCount = dict[str, int]
Depth = int


class IDEDataQubit(pydantic.BaseModel):
    id: int
    numChildren: Optional[int] = None
    name: Optional[str] = None


class IDEQubitDef(pydantic.BaseModel):
    qId: int


class RegisterType(IntEnum):
    QUBIT = 0
    CLASSICAL = 1


class IDEClassicalBitDef(pydantic.BaseModel):
    type: RegisterType
    qId: int
    cId: int


class DataAttributes(pydantic.BaseModel):
    tooltip: Optional[GeneratedFunction] = None
    expanded: str = ""
    controlStates: str = ""
    id: str = ""
    zoom_out: str = ""
    zoom_in: str = ""


class ConditionalRender(IntEnum):
    ALWAYS = 0
    ON_ZERO = 1
    ON_ONE = 2
    AS_GROUP = 3


class IDEDataOperation(pydantic.BaseModel):
    gate: str
    displayName: str
    children: list["IDEDataOperation"]
    depth: Depth
    width: int
    gate_count: GateCount
    _qubits: list = pydantic.PrivateAttr()  # list[Qubit]

    displayArgs: str = ""
    targets: Union[list[IDEQubitDef], list[IDEClassicalBitDef]] = pydantic.Field(
        default_factory=list
    )
    controls: list[IDEQubitDef] = list()
    dataAttributes: DataAttributes = pydantic.Field(default_factory=DataAttributes)
    isControlled: bool = False
    isMeasurement: bool = False
    isConditional: bool = False
    isAdjoint: bool = False
    conditional_render: Optional[ConditionalRender] = None

    @property
    def qubits(self) -> list:  # list[Qubit]
        return self._qubits


class IDEDataProperties(pydantic.BaseModel):
    color: Optional[str] = None
    rightLabel: Optional[str] = None
    leftLabel: Optional[str] = None


class RegisterData(pydantic.BaseModel):
    segmentIds: list[str]
    properties: IDEDataProperties
    registerId: str


class InterfaceSegmentData(pydantic.BaseModel):
    segmentId: str
    properties: IDEDataProperties


class IDEData(VersionedModel):
    qubits: list[IDEDataQubit]
    operations: list[IDEDataOperation]
    register_data: list[RegisterData]
    segment_data: list[InterfaceSegmentData]
    circuit_metrics: Optional[CircuitMetrics]
    hardware_data: SynthesisHardwareData
    creation_time: str
