import ast
from typing import TYPE_CHECKING, Optional

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.functions.classical_type import Bool
from classiq.interface.model.quantum_type import QuantumScalar

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import QmodType, is_classical_type
from classiq.model_expansions.arithmetic import NumericAttributes


def get_numeric_attrs(
    expr_val: QmodAnnotatedExpression,
    node: ast.AST,
    qmod_type: QmodType,
    machine_precision: int,
    treat_qnum_as_float: bool,
) -> Optional[NumericAttributes]:
    if isinstance(qmod_type, Bool):
        return NumericAttributes.from_bounds(0, 1, 0, machine_precision)
    if is_classical_type(qmod_type):
        value = get_classical_value_for_arithmetic(
            expr_val, node, qmod_type, treat_qnum_as_float
        )
        if value is None:
            return None
        return NumericAttributes.from_constant(value, machine_precision)

    if TYPE_CHECKING:
        assert isinstance(qmod_type, QuantumScalar)
    if not qmod_type.is_evaluated:
        return None
    return NumericAttributes.from_quantum_scalar(qmod_type, machine_precision)


def get_classical_value_for_arithmetic(
    expr_val: QmodAnnotatedExpression,
    node: ast.AST,
    qmod_type: QmodType,
    treat_qnum_as_float: bool,
) -> Optional[float]:
    if not is_classical_type(qmod_type):
        return None
    if not expr_val.has_value(node):
        return None

    value = expr_val.get_value(node)
    if not isinstance(value, (int, float)):
        if treat_qnum_as_float and isinstance(value, complex):
            return None
        raise ClassiqExpansionError(
            "Arithmetic of quantum variables and non-real values is not supported"
        )

    return float(value)
