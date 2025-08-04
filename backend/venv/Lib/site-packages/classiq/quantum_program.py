from typing import Optional

from classiq.interface.executor.quantum_program_params import (
    ParameterAssignmentsParams,
    TranspilationParams,
)
from classiq.interface.generator.model.preferences.preferences import Preferences
from classiq.interface.generator.quantum_program import (
    QuantumProgram,
)

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper
from classiq.qmod.builtins.classical_execution_primitives import ExecutionParams


async def transpile_async(params: TranspilationParams) -> QuantumProgram:
    return await ApiWrapper.call_transpilation_task(params)


def transpile(
    quantum_program: QuantumProgram, preferences: Optional[Preferences] = None
) -> QuantumProgram:
    """
    Transpiles a quantum program.

    Args:
        quantum_program: The quantum program to transpile. This is the result of the synthesize method.
        preferences: The transpilation preferences.

    Returns:
        QuantumProgram: The result of the transpilation (Optional).
    """
    if preferences is None:
        preferences = Preferences()
    return async_utils.run(
        transpile_async(
            TranspilationParams(
                quantum_program=quantum_program, preferences=preferences
            )
        )
    )


async def assign_parameters_async(params: ParameterAssignmentsParams) -> QuantumProgram:
    return await ApiWrapper.call_assign_parameters_task(params)


def assign_parameters(
    quantum_program: QuantumProgram, parameters: ExecutionParams
) -> QuantumProgram:
    """
    Assign parameters to a parametric quantum program.

    Args:
        quantum_program: The quantum program to be assigned. This is the result of the synthesize method.
        parameters: The parameter assignments.

    Returns:
        QuantumProgram: The quantum program after assigning parameters.
    """

    return async_utils.run(
        assign_parameters_async(
            ParameterAssignmentsParams(
                quantum_program=quantum_program, parameters=parameters
            )
        )
    )
