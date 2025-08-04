import ast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_type import Integer, Real
from classiq.interface.model.quantum_type import QuantumNumeric

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.numeric_attrs_utils import (
    get_numeric_attrs,
)
from classiq.evaluators.qmod_node_evaluators.utils import (
    QmodType,
    is_classical_integer,
    is_classical_type,
    is_numeric_type,
)
from classiq.model_expansions.arithmetic import NumericAttributes
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_max,
    compute_result_attrs_min,
)


def _infer_min_max_op_type(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    func_name: str,
    args_types: list[QmodType],
    treat_qnum_as_float: bool,
    machine_precision: int,
) -> QmodType:
    if all(is_classical_type(arg_type) for arg_type in args_types):
        if all(is_classical_integer(arg_type) for arg_type in args_types):
            return Integer()
        return Real()

    args_attrs: list[NumericAttributes] = []
    for arg, arg_type in zip(node.args, args_types):
        attrs = get_numeric_attrs(
            expr_val, arg, arg_type, machine_precision, treat_qnum_as_float
        )
        if attrs is None:
            return QuantumNumeric()
        args_attrs.append(attrs)

    if func_name == "min":
        result_attrs = compute_result_attrs_min(args_attrs, machine_precision)
    elif func_name == "max":
        result_attrs = compute_result_attrs_max(args_attrs, machine_precision)
    else:
        raise ClassiqInternalExpansionError

    return result_attrs.to_quantum_numeric()


def eval_min_max_op(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    func_name: str,
    treat_qnum_as_float: bool,
    machine_precision: int,
) -> None:
    if len(node.args) < 1:
        raise ClassiqExpansionError(f"{func_name!r} expects at least one argument")

    args_types = [expr_val.get_type(arg) for arg in node.args]
    if not all(is_numeric_type(arg_type) for arg_type in args_types):
        raise ClassiqExpansionError(
            f"All arguments of {func_name!r} must be scalar values"
        )

    inferred_type = _infer_min_max_op_type(
        expr_val,
        node,
        func_name,
        args_types,
        treat_qnum_as_float,
        machine_precision,
    )
    expr_val.set_type(node, inferred_type)

    if all(expr_val.has_value(arg) for arg in node.args):
        values = [expr_val.get_value(arg) for arg in node.args]
        if not all(isinstance(value, (int, float)) for value in values):
            raise ClassiqExpansionError(f"Invalid argument for function {func_name!r}")

        if func_name == "min":
            result_value = min(*values)
        elif func_name == "max":
            result_value = max(*values)
        else:
            raise ClassiqInternalExpansionError

        expr_val.set_value(node, result_value)
