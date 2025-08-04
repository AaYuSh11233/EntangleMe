import functools
from typing import Optional

import more_itertools

from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.executor.constants import DEFAULT_RESULT_NAME
from classiq.interface.executor.execution_result import (
    ResultsCollection,
    SavedResultValueType,
    TaggedEstimationResult,
    TaggedExecutionDetails,
)
from classiq.interface.executor.quantum_code import Arguments, MultipleArguments

from classiq import QuantumProgram
from classiq.applications.combinatorial_helpers.pauli_helpers.pauli_utils import (
    pauli_operator_to_hamiltonian,
    pauli_operator_to_sparse_hamiltonian,
)
from classiq.execution.execution_session import ExecutionSession

_MAX_ARGUMENTS_SIZE = 1024


def _execute_qnn_estimate(
    session: ExecutionSession,
    arguments: list[Arguments],
    observable: PauliOperator,
) -> ResultsCollection:
    hamiltonian = pauli_operator_to_sparse_hamiltonian(
        pauli_operator_to_hamiltonian(observable.pauli_list)
    )
    return [
        TaggedEstimationResult(
            name=DEFAULT_RESULT_NAME,
            value=result,
            value_type=SavedResultValueType.EstimationResult,
        )
        for result in session.batch_estimate(
            hamiltonian=hamiltonian, parameters=arguments
        )
    ]


def _execute_qnn_sample(
    session: ExecutionSession,
    arguments: list[Arguments],
) -> ResultsCollection:
    return [
        TaggedExecutionDetails(
            name=DEFAULT_RESULT_NAME,
            value=result,
            value_type=SavedResultValueType.ExecutionDetails,
        )
        for result in session.batch_sample(arguments)
    ]


def execute_qnn(
    quantum_program: QuantumProgram,
    arguments: MultipleArguments,
    observable: Optional[PauliOperator] = None,
) -> ResultsCollection:
    with ExecutionSession(quantum_program) as session:
        if observable:
            execute_function = functools.partial(
                _execute_qnn_estimate,
                session=session,
                observable=observable,
            )
        else:
            execute_function = functools.partial(
                _execute_qnn_sample,
                session=session,
            )

        result: ResultsCollection = []
        for chunk in more_itertools.chunked(arguments, _MAX_ARGUMENTS_SIZE):
            chunk_result = execute_function(arguments=chunk)
            result.extend(chunk_result)
        return result
