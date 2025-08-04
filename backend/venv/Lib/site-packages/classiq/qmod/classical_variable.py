import sys
from typing import TYPE_CHECKING, Any

from classiq.interface.exceptions import ClassiqInternalError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import Bool, ClassicalType
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
    ArithmeticOperationKind,
)
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)

from classiq.qmod.cparam import CBool, CParam, CParamScalar
from classiq.qmod.qmod_variable import QBit, _infer_variable_name
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.symbolic import symbolic_function
from classiq.qmod.symbolic_type import SYMBOLIC_TYPES
from classiq.qmod.utilities import get_source_ref


def declare_classical_variable(
    name: str, classical_type: ClassicalType, frame_depth: int
) -> None:
    if TYPE_CHECKING:
        assert QCallable.CURRENT_EXPANDABLE is not None
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        VariableDeclarationStatement(
            name=name,
            qmod_type=classical_type,
            source_ref=get_source_ref(sys._getframe(frame_depth)),
        )
    )


def assign_classical_variable(target: CParam, value: Any, frame_depth: int) -> None:
    if not isinstance(value, SYMBOLIC_TYPES):
        raise TypeError(f"Invalid argument {value!r} for classical variable assignment")

    if TYPE_CHECKING:
        assert QCallable.CURRENT_EXPANDABLE is not None
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        ArithmeticOperation(
            expression=Expression(expr=str(value)),
            result_var=HandleBinding(name=str(target)),
            operation_kind=ArithmeticOperationKind.Assignment,
            source_ref=get_source_ref(sys._getframe(frame_depth)),
        )
    )


def measure(var: QBit) -> CParamScalar:
    """
    Measures the given qubit. `measure` is a non-unitary operation.

    Args:
        var: a qubit variable

    Returns:
        the measurement result (a symbolic boolean variable)
    """
    name = _infer_variable_name(None, 2)
    if name is None:
        raise ClassiqInternalError("Could not infer measure var name")
    declare_classical_variable(name, Bool(), 2)
    res_var = CParamScalar(name)
    res_val = symbolic_function(
        var,
        return_type=CBool,  # type:ignore[type-abstract]
    )
    assign_classical_variable(res_var, res_val, 2)
    return res_var
