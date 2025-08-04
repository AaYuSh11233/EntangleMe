"""Executor module, implementing facilities for executing quantum programs using Classiq platform."""

from typing import Union

from typing_extensions import TypeAlias

from classiq.interface.backend.backend_preferences import BackendPreferencesTypes
from classiq.interface.executor.estimation import OperatorsEstimation
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.executor.quantum_code import QuantumCode
from classiq.interface.executor.quantum_instruction_set import QuantumInstructionSet
from classiq.interface.executor.result import ExecutionDetails
from classiq.interface.generator.quantum_program import (
    QuantumProgram,
)

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper
from classiq.execution.jobs import ExecutionJob

BatchExecutionResult: TypeAlias = Union[ExecutionDetails, BaseException]
ProgramAndResult: TypeAlias = tuple[QuantumCode, BatchExecutionResult]
BackendPreferencesAndResult: TypeAlias = tuple[
    BackendPreferencesTypes, int, BatchExecutionResult
]


async def execute_async(quantum_program: QuantumProgram) -> ExecutionJob:
    execution_input = await ApiWrapper.call_convert_quantum_program(quantum_program)
    result = await ApiWrapper.call_execute_execution_input(execution_input)
    return ExecutionJob(details=result)


def execute(quantum_program: QuantumProgram) -> ExecutionJob:
    """
    Execute a quantum program. The preferences for execution are set on the quantum program using the method `set_execution_preferences`.

    Args:
        quantum_program: The quantum program to execute. This is the result of the synthesize method.

    Returns:
        ExecutionJob: The result of the execution.

    For examples please see [Execution Documentation](https://docs.classiq.io/latest/user-guide/execution/)
    """
    return async_utils.run(execute_async(quantum_program))


def set_quantum_program_execution_preferences(
    quantum_program: QuantumProgram,
    preferences: ExecutionPreferences,
) -> QuantumProgram:
    quantum_program.model.execution_preferences = preferences
    return quantum_program


__all__ = [
    "OperatorsEstimation",
    "QuantumCode",
    "QuantumInstructionSet",
    "set_quantum_program_execution_preferences",
]
