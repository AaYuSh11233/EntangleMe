import ast
from typing import TYPE_CHECKING

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_type import Bool, Integer, Real
from classiq.interface.model.quantum_type import QuantumNumeric

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.numeric_attrs_utils import (
    get_classical_value_for_arithmetic,
    get_numeric_attrs,
)
from classiq.evaluators.qmod_node_evaluators.utils import (
    IntegerValueType,
    NumberValueType,
    QmodType,
    is_classical_integer,
    is_classical_type,
    is_numeric_type,
)
from classiq.model_expansions.arithmetic import NumericAttributes
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_add,
    compute_result_attrs_bitwise_and,
    compute_result_attrs_bitwise_or,
    compute_result_attrs_bitwise_xor,
    compute_result_attrs_lshift,
    compute_result_attrs_modulo,
    compute_result_attrs_multiply,
    compute_result_attrs_power,
    compute_result_attrs_rshift,
    compute_result_attrs_subtract,
)


def _binary_op_allowed(left: QmodType, right: QmodType, op: ast.AST) -> bool:
    left_numeric = is_numeric_type(left)
    right_numeric = is_numeric_type(right)
    if isinstance(op, (ast.BitOr, ast.BitAnd, ast.BitXor)):
        return (left_numeric or isinstance(left, Bool)) and (
            right_numeric or isinstance(right, Bool)
        )
    return left_numeric and right_numeric


def _validate_binary_op(
    op: ast.AST,
    left_type: QmodType,
    right_type: QmodType,
    treat_qnum_as_float: bool,
) -> None:
    if not _binary_op_allowed(left_type, right_type, op):
        raise ClassiqExpansionError(
            f"Both sides of the binary operator {type(op).__name__!r} must be "
            f"scalar values"
        )
    if isinstance(op, (ast.LShift, ast.RShift)) and (
        isinstance(left_type, Real) or isinstance(right_type, Real)
    ):
        raise ClassiqExpansionError(
            f"Bitshift operation {type(op).__name__!r} on real values is not "
            f"supported"
        )
    if isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)) and (
        isinstance(left_type, Real) or isinstance(right_type, Real)
    ):
        raise ClassiqExpansionError(
            f"Bitwise operation {type(op).__name__!r} on real values is not supported"
        )

    if isinstance(op, ast.MatMult):
        raise ClassiqExpansionError(
            f"Binary operation {type(op).__name__!r} is not supported"
        )

    if not treat_qnum_as_float:
        if isinstance(op, ast.FloorDiv) and (
            not is_classical_type(left_type) or not is_classical_type(right_type)
        ):
            raise ClassiqExpansionError(
                f"{type(op).__name__!r} with quantum variables is not supported"
            )

        if not is_classical_type(right_type) and isinstance(
            op, (ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift)
        ):
            raise ClassiqExpansionError(
                f"Right-hand side of binary operation {type(op).__name__!r} must be classical numeric value"
            )


def _infer_binary_op_type(
    expr_val: QmodAnnotatedExpression,
    node: ast.BinOp,
    left_type: QmodType,
    right_type: QmodType,
    machine_precision: int,
    treat_qnum_as_float: bool,
) -> QmodType:
    op = node.op

    if is_classical_type(left_type) and is_classical_type(right_type):
        if isinstance(left_type, Bool) and isinstance(right_type, Bool):
            return Bool()
        if (
            not isinstance(op, ast.Div)
            and (is_classical_integer(left_type) or isinstance(left_type, Bool))
            and (is_classical_integer(right_type) or isinstance(right_type, Bool))
        ):
            return Integer()
        return Real()

    left_attrs = get_numeric_attrs(
        expr_val, node.left, left_type, machine_precision, treat_qnum_as_float
    )
    right_attrs = get_numeric_attrs(
        expr_val, node.right, right_type, machine_precision, treat_qnum_as_float
    )

    if left_attrs is None or right_attrs is None:
        return QuantumNumeric()

    right_value = get_classical_value_for_arithmetic(
        expr_val, node.right, right_type, treat_qnum_as_float
    )

    if isinstance(op, ast.Add):
        result_attrs = compute_result_attrs_add(
            left_attrs, right_attrs, machine_precision
        )

    elif isinstance(op, ast.Sub):
        result_attrs = compute_result_attrs_subtract(
            left_attrs, right_attrs, machine_precision
        )

    elif isinstance(op, ast.Mult):
        result_attrs = compute_result_attrs_multiply(
            left_attrs, right_attrs, machine_precision
        )

    elif isinstance(op, ast.Div):
        if right_value is None:
            return QuantumNumeric()
        if right_value == 0:
            raise ClassiqExpansionError("Division by zero")
        right_attrs = NumericAttributes.from_constant(
            1 / right_value, machine_precision
        )
        result_attrs = compute_result_attrs_multiply(
            left_attrs, right_attrs, machine_precision
        )
    elif isinstance(op, ast.FloorDiv):
        return QuantumNumeric()

    elif isinstance(op, ast.Mod):
        if right_value is None or treat_qnum_as_float:
            return QuantumNumeric()
        result_attrs = compute_result_attrs_modulo(
            left_attrs, right_value, machine_precision
        )

    elif isinstance(op, ast.Pow):
        if right_value is None or treat_qnum_as_float:
            return QuantumNumeric()
        result_attrs = compute_result_attrs_power(
            left_attrs, right_value, machine_precision
        )

    elif isinstance(op, ast.LShift):
        if right_value is None:
            return QuantumNumeric()
        result_attrs = compute_result_attrs_lshift(
            left_attrs, right_value, machine_precision
        )

    elif isinstance(op, ast.RShift):
        if right_value is None:
            return QuantumNumeric()
        result_attrs = compute_result_attrs_rshift(
            left_attrs, right_value, machine_precision
        )

    elif isinstance(op, ast.BitAnd):
        result_attrs = compute_result_attrs_bitwise_and(
            left_attrs, right_attrs, machine_precision
        )
    elif isinstance(op, ast.BitOr):
        result_attrs = compute_result_attrs_bitwise_or(
            left_attrs, right_attrs, machine_precision
        )

    elif isinstance(op, ast.BitXor):
        result_attrs = compute_result_attrs_bitwise_xor(
            left_attrs, right_attrs, machine_precision
        )
    else:
        raise ClassiqInternalExpansionError

    return result_attrs.to_quantum_numeric()


def _eval_binary_op_constant(
    op: ast.AST, left_value: NumberValueType, right_value: NumberValueType
) -> NumberValueType:
    if isinstance(op, ast.Add):
        return left_value + right_value
    if isinstance(op, ast.Sub):
        return left_value - right_value
    if isinstance(op, ast.Mult):
        return left_value * right_value
    if isinstance(op, ast.Div):
        if right_value == 0:
            raise ClassiqExpansionError("Division by zero")
        return left_value / right_value
    if isinstance(op, ast.FloorDiv):
        if right_value == 0:
            raise ClassiqExpansionError("Integer division by zero")
        if isinstance(left_value, complex) or isinstance(right_value, complex):
            raise ClassiqExpansionError("Integer division with a complex number")
        return left_value // right_value
    if isinstance(op, ast.Mod):
        if right_value == 0:
            raise ClassiqExpansionError("Integer modulo by zero")
        if isinstance(left_value, complex) or isinstance(right_value, complex):
            raise ClassiqExpansionError("Integer modulo with a complex number")
        return left_value % right_value
    if isinstance(op, ast.Pow):
        return left_value**right_value

    if TYPE_CHECKING:
        assert isinstance(left_value, IntegerValueType)
        assert isinstance(right_value, IntegerValueType)

    if isinstance(op, ast.LShift):
        return left_value << right_value
    if isinstance(op, ast.RShift):
        return left_value >> right_value
    if isinstance(op, ast.BitAnd):
        return left_value & right_value
    if isinstance(op, ast.BitOr):
        return left_value | right_value
    if isinstance(op, ast.BitXor):
        return left_value ^ right_value

    raise ClassiqInternalExpansionError


def eval_binary_op(
    expr_val: QmodAnnotatedExpression,
    node: ast.BinOp,
    treat_qnum_as_float: bool,
    machine_precision: int,
) -> None:
    left = node.left
    right = node.right
    op = node.op

    left_type = expr_val.get_type(left)
    right_type = expr_val.get_type(right)
    _validate_binary_op(op, left_type, right_type, treat_qnum_as_float)

    inferred_type = _infer_binary_op_type(
        expr_val,
        node,
        left_type,
        right_type,
        machine_precision,
        treat_qnum_as_float,
    )
    expr_val.set_type(node, inferred_type)

    if expr_val.has_value(left) and expr_val.has_value(right):
        left_value = expr_val.get_value(left)
        right_value = expr_val.get_value(right)
        expr_val.set_value(node, _eval_binary_op_constant(op, left_value, right_value))
