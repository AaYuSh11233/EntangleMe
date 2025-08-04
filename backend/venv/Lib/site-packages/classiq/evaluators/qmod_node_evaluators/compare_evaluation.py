import ast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
    QuantumScalar,
)

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.list_evaluation import list_allowed
from classiq.evaluators.qmod_node_evaluators.utils import (
    QmodType,
    element_types,
    is_classical_integer,
    is_classical_type,
    qnum_is_qbit,
)


def comparison_allowed(
    left: QmodType, right: QmodType, inequality: bool = False
) -> bool:
    if isinstance(left, Bool):
        return isinstance(right, (Bool, Integer, QuantumBit)) or (
            isinstance(right, QuantumNumeric) and qnum_is_qbit(right)
        )
    if isinstance(left, Real) or is_classical_integer(left):
        return isinstance(right, (Real, Bool, QuantumScalar)) or is_classical_integer(
            right
        )
    if isinstance(left, (ClassicalArray, ClassicalTuple)):
        if inequality:
            return False
        if not isinstance(right, (ClassicalArray, ClassicalTuple)):
            return False
        return list_allowed(element_types(left) + element_types(right))
    if isinstance(left, TypeName):
        return (
            left.has_classical_struct_decl
            and not inequality
            and isinstance(right, TypeName)
            and left.name == right.name
        ) or (
            left.is_enum
            and (
                isinstance(right, (Integer, Real, QuantumScalar))
                or (isinstance(right, TypeName) and right.is_enum)
            )
        )
    if isinstance(left, QuantumScalar):
        return isinstance(right, (Bool, Real, QuantumScalar)) or is_classical_integer(
            right
        )
    if isinstance(left, QuantumBitvector):
        return False
    raise ClassiqInternalExpansionError


def eval_compare(expr_val: QmodAnnotatedExpression, node: ast.Compare) -> None:
    left = node.left
    if len(node.ops) != 1 or len(node.comparators) != 1:
        raise ClassiqExpansionError("Multi-compare expressions are not supported")
    right = node.comparators[0]
    op = node.ops[0]

    left_type = expr_val.get_type(left)
    right_type = expr_val.get_type(right)
    if not comparison_allowed(left_type, right_type, not isinstance(op, ast.Eq)):
        raise ClassiqExpansionError(
            f"Cannot compare {left_type.qmod_type_name} {ast.unparse(left)!r} "
            f"and {right_type.qmod_type_name} {ast.unparse(right)!r}"
        )
    qmod_type: QmodType
    if not is_classical_type(left_type) or not is_classical_type(right_type):
        qmod_type = QuantumBit()
    else:
        qmod_type = Bool()
    expr_val.set_type(node, qmod_type)

    if not expr_val.has_value(left) or not expr_val.has_value(right):
        return

    left_value = expr_val.get_value(left)
    right_value = expr_val.get_value(right)
    if isinstance(op, ast.Eq):
        expr_val.set_value(node, left_value == right_value)
    elif isinstance(op, ast.NotEq):
        expr_val.set_value(node, left_value != right_value)
    elif isinstance(op, ast.Lt):
        expr_val.set_value(node, left_value < right_value)
    elif isinstance(op, ast.Gt):
        expr_val.set_value(node, left_value > right_value)
    elif isinstance(op, ast.LtE):
        expr_val.set_value(node, left_value <= right_value)
    elif isinstance(op, ast.GtE):
        expr_val.set_value(node, left_value >= right_value)
    else:
        raise ClassiqExpansionError(f"Unsupported comparison {type(op).__name__!r}")
