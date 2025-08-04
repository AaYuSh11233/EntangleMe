import json
from collections import Counter
from collections.abc import Iterator
from functools import cached_property
from itertools import count
from typing import Any, Optional

import pydantic
from pydantic import ConfigDict, field_validator

from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.generated_circuit_data import (
    OperationLevel,
)
from classiq.interface.generator.hardware.hardware_data import SynthesisHardwareData
from classiq.interface.helpers.versioned_model import VersionedModel


class OperationIdCounter:
    _op_id_counter: Iterator[int] = count()

    def next_id(self) -> int:
        return next(self._op_id_counter)

    def reset_operation_counter(self) -> None:
        self._op_id_counter = count()


_operation_id_counter = OperationIdCounter()


def reset_operation_counter() -> None:
    """
    Call this at the start of every new task to restart ids at 0.
    """
    _operation_id_counter.reset_operation_counter()


class OperationType(StrEnum):
    REGULAR = "REGULAR"
    INVISIBLE = "INVISIBLE"
    ALLOCATE = "ALLOCATE"
    FREE = "FREE"
    BIND = "BIND"
    ATOMIC = "ATOMIC"


class OperationData(pydantic.BaseModel):
    approximated_depth: Optional[int] = None
    width: int
    gate_count: Counter[str] = pydantic.Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


class CircuitMetrics(pydantic.BaseModel):
    depth: int
    count_ops: dict[str, int]


class ProgramData(pydantic.BaseModel):
    hardware_data: SynthesisHardwareData
    circuit_metrics: CircuitMetrics


class OperationLink(pydantic.BaseModel):
    label: str
    inner_label: Optional[str] = None
    qubits: tuple[int, ...]
    type: str
    is_captured: bool = False

    model_config = ConfigDict(frozen=True)

    def __hash__(self) -> int:
        return hash((type(self), self.label, self.qubits, self.type))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OperationLink):
            return False
        return hash(self) == hash(other)


class OperationLinks(pydantic.BaseModel):
    inputs: list[OperationLink]
    outputs: list[OperationLink]

    model_config = ConfigDict(frozen=True)

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def sort_links(cls, v: list[OperationLink]) -> Any:
        """
        sorting the input/output links on creation
        the sort is done by 'label-qubits-type'
        since hash is non-deterministic between runs
        """
        return sorted(v, key=hash)

    def __hash__(self) -> int:
        return hash(json.dumps(self.model_dump(exclude_none=True), sort_keys=True))

    @cached_property
    def input_width(self) -> int:
        return sum(len(link.qubits) for link in self.inputs)

    @cached_property
    def output_width(self) -> int:
        return sum(len(link.qubits) for link in self.outputs)


class AtomicGate(StrEnum):
    UNKNOWN = ""
    H = "H"
    X = "X"
    Y = "Y"
    Z = "Z"
    I = "I"  # noqa: E741
    S = "S"
    T = "T"
    SDG = "SDG"
    TDG = "TDG"
    PHASE = "PHASE"
    RX = "RX"
    RY = "RY"
    RZ = "RZ"
    R = "R"
    RXX = "RXX"
    RYY = "RYY"
    RZZ = "RZZ"
    CH = "CH"
    CX = "CX"
    CY = "CY"
    CZ = "CZ"
    CRX = "CRX"
    CRY = "CRY"
    CRZ = "CRZ"
    CPHASE = "CPHASE"
    SWAP = "SWAP"
    IDENTITY = "IDENTITY"
    U = "U"
    RESET = "RESET"

    @property
    def is_control_gate(self) -> bool:
        return self.startswith("C")


class Operation(pydantic.BaseModel):
    name: str
    inner_label: Optional[str] = None
    _id: int = pydantic.PrivateAttr(default_factory=_operation_id_counter.next_id)
    qasm_name: str = pydantic.Field(default="")
    details: str = pydantic.Field(default="")
    children: list["Operation"] = pydantic.Field(default_factory=list)
    # children_ids is optional in order to support backwards compatibility.
    children_ids: list[int] = pydantic.Field(default_factory=list)
    operation_data: Optional[OperationData] = None
    operation_links: OperationLinks
    control_qubits: tuple[int, ...] = pydantic.Field(default_factory=tuple)
    auxiliary_qubits: tuple[int, ...]
    target_qubits: tuple[int, ...]
    operation_level: OperationLevel
    operation_type: OperationType = pydantic.Field(
        description="Identifies unique operations that are visualized differently",
    )
    gate: AtomicGate = pydantic.Field(
        default=AtomicGate.UNKNOWN, description="Gate type"
    )
    is_daggered: bool = pydantic.Field(default=False)
    expanded: bool = pydantic.Field(default=False)
    show_expanded_label: bool = pydantic.Field(default=False)
    is_low_level_fallback: bool = pydantic.Field(default=False)

    model_config = ConfigDict(frozen=True)

    @property
    def id(self) -> int:
        return self._id

    def __hash__(self) -> int:
        """
        using a custom hashable_dict in order to compare the operation
        with the qubits in order
        """
        js = json.dumps(
            self._hashable_dict(),
            sort_keys=True,
            default=lambda o: o.value if hasattr(o, "value") else str(o),
        )
        return hash(js)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Operation)
            and self._hashable_dict() == other._hashable_dict()
        )

    def _hashable_dict(self) -> dict:
        data = self.model_dump(
            exclude_none=True,
        )
        # force qubit order for equality
        for key in ("target_qubits", "auxiliary_qubits", "control_qubits"):
            data[key] = sorted(data[key])
        return data


class ProgramVisualModel(VersionedModel):
    main_operation: Operation = pydantic.Field(default=None)
    id_to_operations: dict[int, Operation] = pydantic.Field(default_factory=dict)
    main_operation_id: int = pydantic.Field(default=None)
    program_data: ProgramData

    @property
    def main_op_from_mapping(self) -> Operation:
        if self.main_operation_id is None:
            raise ValueError("Main operation ID is not set.")
        return self.id_to_operations[self.main_operation_id]
