from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

import pydantic
from pydantic import BaseModel, ConfigDict
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.backend.ionq.ionq_quantum_program import IonqQuantumCircuit
from classiq.interface.backend.pydantic_backend import PydanticArgumentNameType
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.executor.quantum_instruction_set import QuantumInstructionSet
from classiq.interface.executor.register_initialization import RegisterInitialization
from classiq.interface.generator.synthesis_metadata.synthesis_execution_data import (
    ExecutionData,
)

Arguments = dict[PydanticArgumentNameType, Any]
MultipleArguments = tuple[Arguments, ...]
CodeType = str
RegistersInitialization = dict[str, RegisterInitialization]
Qubits = tuple[int, ...]
OutputQubitsMap = dict[str, Qubits]


class QuantumBaseCode(BaseModel):
    syntax: QuantumInstructionSet = pydantic.Field(
        default=QuantumInstructionSet.QASM, description="The syntax of the program."
    )
    code: CodeType = pydantic.Field(
        ..., description="The textual representation of the program"
    )

    @pydantic.field_validator("code")
    @classmethod
    def load_quantum_program(
        cls, code: Union[CodeType, IonqQuantumCircuit], values: ValidationInfo
    ) -> CodeType:
        syntax = values.data.get("syntax")
        if isinstance(code, IonqQuantumCircuit):
            if syntax != QuantumInstructionSet.IONQ:
                raise ClassiqValueError(
                    f"Invalid code type {type(code)} for syntax: {syntax}"
                )
            return code.model_dump_json()

        return code


class QuantumCode(QuantumBaseCode):
    arguments: MultipleArguments = pydantic.Field(
        default=(),
        description="The parameters dictionary for a parametrized quantum program.",
    )
    output_qubits_map: OutputQubitsMap = pydantic.Field(
        default_factory=dict,
        description="The map of outputs to their qubits in the circuit.",
    )
    registers_initialization: Optional[RegistersInitialization] = pydantic.Field(
        default=None,
        description="Initial conditions for the different registers in the circuit.",
    )
    synthesis_execution_data: Optional[ExecutionData] = pydantic.Field(default=None)
    synthesis_execution_arguments: Arguments = pydantic.Field(default_factory=dict)
    model_config = ConfigDict(validate_assignment=True)

    @pydantic.field_validator("arguments", mode="before")
    @classmethod
    def validate_arguments(
        cls, arguments: MultipleArguments, info: ValidationInfo
    ) -> MultipleArguments:
        if arguments and info.data.get("syntax") not in (
            QuantumInstructionSet.QSHARP,
            QuantumInstructionSet.QASM,
        ):
            raise ClassiqValueError("Only QASM or Q# programs support arguments")

        if (
            info.data.get("syntax") == QuantumInstructionSet.QSHARP
            and len(arguments) > 1
        ):
            raise ClassiqValueError(
                f"Q# programs supports only one group of arguments. {len(arguments)} given"
            )

        return arguments

    @pydantic.field_validator("synthesis_execution_data")
    @classmethod
    def validate_synthesis_execution_data(
        cls,
        synthesis_execution_data: Optional[ExecutionData],
        values: ValidationInfo,
    ) -> Optional[ExecutionData]:
        if (
            synthesis_execution_data is not None
            and synthesis_execution_data.function_execution
        ) and values.data.get("syntax") is not QuantumInstructionSet.QASM:
            raise ClassiqValueError("Only QASM supports the requested configuration")

        return synthesis_execution_data

    @staticmethod
    def from_file(
        file_path: Union[str, Path],
        syntax: Optional[Union[str, QuantumInstructionSet]] = None,
        arguments: MultipleArguments = (),
    ) -> QuantumCode:
        path = Path(file_path)
        code = path.read_text()
        if syntax is None:
            syntax = QuantumInstructionSet.from_suffix(path.suffix.lstrip("."))
        return QuantumCode(syntax=syntax, code=code, arguments=arguments)
