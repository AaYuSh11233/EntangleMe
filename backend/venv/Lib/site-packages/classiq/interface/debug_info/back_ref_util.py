from classiq.interface.model.allocate import Allocate
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.statement_block import (
    ConcreteQuantumStatement,
    StatementBlock,
)

"""
This module contains helper functions to determine if a given quantum statement
 is an allocation or free statement.
"""


def is_allocate_or_free(concrete_quantum_statement: ConcreteQuantumStatement) -> bool:
    return isinstance(concrete_quantum_statement, Allocate) or (
        isinstance(concrete_quantum_statement, QuantumFunctionCall)
        and concrete_quantum_statement.function == "free"
    )


def is_allocate_or_free_by_backref(back_refs: StatementBlock) -> bool:
    return len(back_refs) > 0 and is_allocate_or_free(back_refs[0])
