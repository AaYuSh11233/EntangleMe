import ast
from functools import reduce
from operator import and_, or_

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_type import Bool
from classiq.interface.model.quantum_type import QuantumBit, QuantumNumeric

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import (
    QmodType,
    is_classical_type,
    qnum_is_qbit,
)


def bool_op_allowed(left: QmodType, right: QmodType) -> bool:
    return is_bool_type(left) and is_bool_type(right)


def is_bool_type(qmod_type: QmodType) -> bool:
    if isinstance(qmod_type, QuantumNumeric):
        return qnum_is_qbit(qmod_type)
    elif not isinstance(qmod_type, (QuantumBit, Bool)):
        return False
    return True


def eval_bool_op(expr_val: QmodAnnotatedExpression, node: ast.BoolOp) -> None:
    if len(node.values) < 2:
        raise ClassiqInternalExpansionError

    left = node.values[0]
    rights = node.values[0:]
    op = node.op

    left_type = expr_val.get_type(left)
    right_types = [expr_val.get_type(right) for right in rights]
    if not all(bool_op_allowed(left_type, right_type) for right_type in right_types):
        raise ClassiqExpansionError(
            f"Both sides of the Boolean operator {type(op).__name__!r} must be "
            f"Boolean values"
        )
    qmod_type: QmodType
    if not is_classical_type(left_type) or not all(
        is_classical_type(right_type) for right_type in right_types
    ):
        qmod_type = QuantumBit()
    else:
        qmod_type = Bool()
    expr_val.set_type(node, qmod_type)

    if not expr_val.has_value(left) or not all(
        expr_val.has_value(right) for right in rights
    ):
        return

    left_value = expr_val.get_value(left)
    right_values = [expr_val.get_value(right) for right in rights]
    if isinstance(op, ast.And):
        operator = and_
    elif isinstance(op, ast.Or):
        operator = or_
    else:
        raise ClassiqInternalExpansionError
    constant_value = reduce(operator, [left_value, *right_values])
    expr_val.set_value(node, constant_value)
