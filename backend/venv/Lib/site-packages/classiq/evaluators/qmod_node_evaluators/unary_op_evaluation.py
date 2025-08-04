import ast
from typing import TYPE_CHECKING, Any

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_type import Integer, Real
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.quantum_type import (
    QuantumNumeric,
    QuantumScalar,
)

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.bool_op_evaluation import is_bool_type
from classiq.evaluators.qmod_node_evaluators.utils import (
    QmodType,
    is_classical_type,
    is_numeric_type,
)
from classiq.model_expansions.arithmetic import NumericAttributes
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_bitwise_invert,
    compute_result_attrs_negate,
)


def unary_op_allowed(op: ast.AST, operand_type: QmodType) -> bool:
    if isinstance(op, ast.Not):
        return is_bool_type(operand_type)
    return is_numeric_type(operand_type)


def _infer_unary_op_type(
    op: ast.AST, operand_type: QmodType, machine_precision: int
) -> QmodType:
    if is_classical_type(operand_type):
        if isinstance(operand_type, TypeName):
            # The operand is enum, return as integer
            return Integer()
        return operand_type

    if TYPE_CHECKING:
        assert isinstance(operand_type, QuantumScalar)

    if isinstance(op, (ast.Not, ast.UAdd)):
        return operand_type

    if not operand_type.is_evaluated:
        return QuantumNumeric()

    operand_attrs = NumericAttributes.from_quantum_scalar(
        operand_type, machine_precision
    )
    if isinstance(op, ast.Invert):
        result_attrs = compute_result_attrs_bitwise_invert(
            operand_attrs, machine_precision
        )
    elif isinstance(op, ast.USub):
        result_attrs = compute_result_attrs_negate(operand_attrs, machine_precision)
    else:
        raise ClassiqInternalExpansionError

    return result_attrs.to_quantum_numeric()


def eval_unary_op(
    expr_val: QmodAnnotatedExpression, node: ast.UnaryOp, machine_precision: int
) -> None:
    operand = node.operand
    op = node.op

    operand_type = expr_val.get_type(operand)
    if not unary_op_allowed(op, operand_type):
        expected_val_type = "Boolean" if isinstance(op, ast.Not) else "scalar"
        raise ClassiqExpansionError(
            f"The operand of the unary operator {type(op).__name__!r} must be "
            f"a {expected_val_type} value"
        )
    if isinstance(op, ast.Invert) and isinstance(operand_type, Real):
        raise ClassiqExpansionError(
            f"Operation {type(op).__name__!r} on a real value is not supported"
        )

    expr_val.set_type(node, _infer_unary_op_type(op, operand_type, machine_precision))

    if not expr_val.has_value(operand):
        return
    operand_value = expr_val.get_value(operand)
    constant_value: Any
    if isinstance(op, ast.Not):
        constant_value = not operand_value
    elif isinstance(op, ast.Invert):
        constant_value = ~operand_value
    elif isinstance(op, ast.UAdd):
        constant_value = +operand_value
    elif isinstance(op, ast.USub):
        constant_value = -operand_value
    else:
        raise ClassiqInternalExpansionError
    expr_val.set_value(node, constant_value)
