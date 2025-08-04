import logging
import re
from typing import Literal, Optional, Union
from uuid import UUID

import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import TypeAlias

from classiq.interface.debug_info.back_ref_util import is_allocate_or_free_by_backref
from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.compiler_keywords import (
    generate_original_function_name,
)
from classiq.interface.generator.control_state import ControlState
from classiq.interface.generator.register_role import RegisterRole
from classiq.interface.generator.synthesis_metadata.synthesis_execution_data import (
    ExecutionData,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperationKind,
)
from classiq.interface.model.statement_block import (
    ArithmeticOperation,
    ConcreteQuantumStatement,
    QuantumFunctionCall,
    StatementBlock,
)

from classiq.model_expansions.capturing.mangling_utils import (
    is_captured_var_name,
)

_logger = logging.getLogger(__name__)
ParameterName = str
IOQubitMapping: TypeAlias = dict[str, tuple[int, ...]]

CLASSIQ_HIERARCHY_SEPARATOR: Literal["__"] = "__"
QASM_SEPARATOR = "_"
SPLIT_MARKER: str = "part"
ARITH_ENGINE_PREFIX = "arith_eng__"
PART_SUFFIX_REGEX = re.compile(
    rf".+{QASM_SEPARATOR}{SPLIT_MARKER}{QASM_SEPARATOR}(\d+)$"
)

VISUALIZATION_HIDE_LIST = [
    "apply_to_all",
    "repeat",
    "control",
    "mcx",
    "iteration",
    "stmt_block",
]


def last_name_in_call_hierarchy(name: str) -> str:
    return name.split(CLASSIQ_HIERARCHY_SEPARATOR)[-1]


class QubitMapping(pydantic.BaseModel):
    logical_inputs: IOQubitMapping = pydantic.Field(default_factory=dict)
    logical_outputs: IOQubitMapping = pydantic.Field(default_factory=dict)
    physical_inputs: IOQubitMapping = pydantic.Field(default_factory=dict)
    physical_outputs: IOQubitMapping = pydantic.Field(default_factory=dict)


class GeneratedRegister(pydantic.BaseModel):
    name: str
    role: RegisterRole
    qubit_indexes_relative: list[int]
    qubit_indexes_absolute: list[int]

    def __len__(self) -> int:
        return self.qubit_indexes_relative.__len__()

    @property
    def width(self) -> int:
        return len(self)

    @property
    def is_captured(self) -> bool:
        return is_captured_var_name(self.name)


class GeneratedFunction(pydantic.BaseModel):
    name: str
    control_states: list[ControlState]
    registers: list[GeneratedRegister] = list()
    depth: Optional[int] = pydantic.Field(default=None)
    width: Optional[int] = pydantic.Field(default=None)
    dangling_inputs: dict[str, GeneratedRegister] = dict()
    dangling_outputs: dict[str, GeneratedRegister] = dict()

    def __getitem__(self, key: Union[int, str]) -> GeneratedRegister:
        if isinstance(key, int):
            return self.registers[key]
        if isinstance(key, str):
            for register in self.registers:
                if key == register.name:
                    return register
        raise KeyError(key)

    def get(self, key: Union[int, str]) -> Optional[GeneratedRegister]:
        try:
            return self.__getitem__(key)
        except KeyError:
            return None

    @property
    def should_appear_in_visualization(self) -> bool:
        return all(
            hide_regex not in last_name_in_call_hierarchy(self.name.lower())
            for hide_regex in VISUALIZATION_HIDE_LIST
        )


class GeneratedCircuitData(pydantic.BaseModel):
    width: int
    circuit_parameters: list[ParameterName] = pydantic.Field(default_factory=list)
    qubit_mapping: QubitMapping = pydantic.Field(default_factory=QubitMapping)
    execution_data: Optional[ExecutionData] = pydantic.Field(default=None)

    @classmethod
    def from_empty_logic_flow(cls) -> "GeneratedCircuitData":
        return cls(width=0)


class OperationLevel(StrEnum):
    QMOD_FUNCTION_CALL = "QMOD_CALL"
    QMOD_STATEMENT = "QMOD_STATEMENT"
    ENGINE_FUNCTION_CALL = "ENGINE_CALL"
    UNKNOWN = "UNKNOWN"


class StatementType(StrEnum):
    CONTROL = "control"
    POWER = "power"
    INVERT = "invert"
    WITHIN_APPLY = "within apply"
    WITHIN = "within"
    APPLY = "apply"
    ASSIGN = "assign"
    ASSIGN_AMPLITUDE = "assign amplitude"
    PHASE = "phase"
    INPLACE_XOR = "inplace xor"
    INPLACE_ADD = "inplace add"
    REPEAT = "repeat"
    BLOCK = "block"
    IF = "if"


# Mapping between statement kind (or sub-kind) and statement type (visualization name)
# Keys (statement kind) are taken from the `kind` field of the statement models,
# which cannot be used directly because they're instance fields of `Literal` type.
STATEMENTS_NAME: dict[str, StatementType] = {
    "Control": StatementType.CONTROL,
    "Power": StatementType.POWER,
    "Invert": StatementType.INVERT,
    "WithinApply": StatementType.WITHIN_APPLY,
    "Compute": StatementType.WITHIN,
    "Action": StatementType.APPLY,
    "Uncompute": StatementType.WITHIN,
    ArithmeticOperationKind.Assignment.value: StatementType.ASSIGN,
    "InplaceBinaryOperation": StatementType.ASSIGN,
    "AmplitudeLoadingOperation": StatementType.ASSIGN_AMPLITUDE,
    "PhaseOperation": StatementType.PHASE,
    ArithmeticOperationKind.InplaceXor.value: StatementType.INPLACE_XOR,
    ArithmeticOperationKind.InplaceAdd.value: StatementType.INPLACE_ADD,
    "Repeat": StatementType.REPEAT,
    "Block": StatementType.BLOCK,
    "ClassicalIf": StatementType.IF,
}


class FunctionDebugInfoInterface(pydantic.BaseModel):
    generated_function: Optional[GeneratedFunction] = Field(default=None)
    children: list["FunctionDebugInfoInterface"]
    relative_qubits: tuple[int, ...]
    absolute_qubits: Optional[tuple[int, ...]] = Field(default=None)
    control_variable: Optional[str] = Field(default=None)
    is_basis_gate: Optional[bool] = Field(default=None)
    is_inverse: bool = Field(default=False)
    is_unitary: bool = Field(default=True, exclude=True)
    uuid: Optional[UUID] = Field(default=None, exclude=True)
    port_to_passed_variable_map: dict[str, str] = Field(default={})
    back_refs: StatementBlock = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
    # Temporary field to store the override debug info for parallel old/new visualization
    override_debug_info: Optional["FunctionDebugInfoInterface"] = None

    @property
    def is_allocate_or_free(self) -> bool:
        return is_allocate_or_free_by_backref(self.back_refs)

    @property
    def name(self) -> str:
        generated_name = self.generated_function.name if self.generated_function else ""
        # Temp fix for remaining old "supported" statements - power
        if generated_name == StatementType.POWER:
            return generated_name

        back_ref = self.first_back_ref
        if back_ref is None:
            return generated_name

        if isinstance(back_ref, QuantumFunctionCall):
            name = generate_original_function_name(back_ref.func_name).removeprefix(
                ARITH_ENGINE_PREFIX
            )
            name_with_suffix = self.add_suffix_from_generated_name(generated_name, name)
            return name_with_suffix

        statement_kind: str = back_ref.kind
        if isinstance(back_ref, ArithmeticOperation):
            statement_kind = back_ref.operation_kind.value
        return self.add_suffix_from_generated_name(
            generated_name, STATEMENTS_NAME[statement_kind]
        )

    def add_suffix_from_generated_name(self, generated_name: str, name: str) -> str:
        if part_match := PART_SUFFIX_REGEX.match(generated_name):
            suffix = f" [{part_match.group(1)}]"
        else:
            suffix = ""
        return f"{name}{suffix}"

    @property
    def first_back_ref(self) -> Optional[ConcreteQuantumStatement]:
        return self.back_refs[0] if self.back_refs else None

    @property
    def level(self) -> OperationLevel:
        # Temp fix for remaining old "supported" statements - power
        if self.name == StatementType.POWER:
            return OperationLevel.QMOD_STATEMENT

        if self.first_back_ref is None:
            # we use ENGINE_FUNCTION_CALL in case where there's not back ref
            return OperationLevel.ENGINE_FUNCTION_CALL

        if isinstance(self.first_back_ref, QuantumFunctionCall):
            return OperationLevel.QMOD_FUNCTION_CALL
        return OperationLevel.QMOD_STATEMENT

    @property
    def registers(self) -> list[GeneratedRegister]:
        if self.generated_function is None:
            return list()
        return self.generated_function.registers

    @property
    def is_controlled(self) -> bool:
        if self.generated_function is None:
            return False
        return len(self.generated_function.control_states) > 0

    @property
    def control_states(self) -> list[ControlState]:
        if self.generated_function is None:
            return list()
        return self.generated_function.control_states

    @property
    def control_qubits(self) -> tuple[int, ...]:
        return tuple(
            qubit
            for register in self.registers
            for qubit in register.qubit_indexes_absolute
            if register.role is RegisterRole.INPUT
            and self.port_to_passed_variable_map.get(register.name, register.name)
            == self.control_variable
        )

    def propagate_absolute_qubits(self) -> "FunctionDebugInfoInterface":
        if self.absolute_qubits is None:
            return self

        updated_registers = [
            register.model_copy(
                update=dict(
                    qubit_indexes_absolute=list(
                        _get_absolute_from_relative(
                            self.absolute_qubits, tuple(register.qubit_indexes_relative)
                        )
                    )
                )
            )
            for register in self.registers
        ]
        updated_generated_function = (
            self.generated_function.model_copy(update=dict(registers=updated_registers))
            if self.generated_function
            else None
        )

        updated_children: list[FunctionDebugInfoInterface] = []
        for child in self.children:
            updated_child = child.white_new_absolute_qubits(self.absolute_qubits)
            if updated_child.override_debug_info is None:
                updated_child = updated_child.propagate_absolute_qubits()
            else:
                updated_child.override_debug_info = (
                    updated_child.override_debug_info.white_new_absolute_qubits(
                        absolute_qubits=self.absolute_qubits
                    ).propagate_absolute_qubits()
                )
            updated_children.append(updated_child)

        return self.model_copy(
            update=dict(
                generated_function=updated_generated_function,
                children=updated_children,
            )
        )

    def white_new_absolute_qubits(
        self, absolute_qubits: tuple[int, ...]
    ) -> "FunctionDebugInfoInterface":
        return self.model_copy(
            update=dict(
                absolute_qubits=_get_absolute_from_relative(
                    absolute_qubits, self.relative_qubits
                )
            )
        )

    def inverse(self) -> "FunctionDebugInfoInterface":
        if self.override_debug_info is not None:
            self.override_debug_info = self.override_debug_info.inverse()
            return self
        inverse_generated_function = (
            self.generated_function.model_copy(
                update=dict(registers=self._inverse_registers)
            )
            if self.generated_function
            else None
        )
        inverted_children = [child.inverse() for child in reversed(self.children)]
        return self.model_copy(
            update=dict(
                is_inverse=not self.is_inverse,
                children=inverted_children,
                generated_function=inverse_generated_function,
            )
        )

    @property
    def _inverse_registers(self) -> list[GeneratedRegister]:
        return [
            reg.model_copy(update=dict(role=self._inverse_register_role(reg.role)))
            for reg in self.registers
        ]

    def _inverse_register_role(self, role: RegisterRole) -> RegisterRole:
        if role is RegisterRole.INPUT:
            return RegisterRole.OUTPUT
        if role is RegisterRole.EXPLICIT_ZERO_INPUT or role is RegisterRole.ZERO_INPUT:
            return RegisterRole.ZERO_OUTPUT
        if role is RegisterRole.AUXILIARY:
            return RegisterRole.AUXILIARY
        if role is RegisterRole.OUTPUT or role is RegisterRole.GARBAGE_OUTPUT:
            return RegisterRole.INPUT
        if role is RegisterRole.ZERO_OUTPUT:
            return RegisterRole.ZERO_INPUT


def _get_absolute_from_relative(
    absolute_qubits: tuple[int, ...], relative_qubits: tuple[int, ...]
) -> tuple[int, ...]:
    if len(relative_qubits) == 0:
        return tuple()
    if max(relative_qubits) >= len(absolute_qubits):
        _logger.warning(
            "Invalid qubit computation (relative qubits: %s, absolute qubits: %s)",
            relative_qubits,
            absolute_qubits,
        )
        return tuple()
    return tuple(absolute_qubits[relative_qubit] for relative_qubit in relative_qubits)
