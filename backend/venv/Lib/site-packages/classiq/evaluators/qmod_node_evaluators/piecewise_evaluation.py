import ast
from collections.abc import Sequence

import sympy

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.functions.classical_type import Bool, Integer, Real

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression


def eval_piecewise(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    args: Sequence[tuple[ast.AST, ast.AST]],
) -> None:
    cond_types = [expr_val.get_type(cond) for _, cond in args]
    if not all(isinstance(cond_type, Bool) for cond_type in cond_types):
        raise ClassiqExpansionError(
            "Piecewise conditions must be classical Boolean values"
        )

    value_types = [expr_val.get_type(value) for value, _ in args]
    if not all(isinstance(value_type, (Integer, Real)) for value_type in value_types):
        raise ClassiqExpansionError("Piecewise values must be classical numeric values")

    if all(isinstance(value_type, Integer) for value_type in value_types):
        expr_val.set_type(node, Integer())
    else:
        expr_val.set_type(node, Real())

    if not all(
        expr_val.has_value(value) and expr_val.has_value(cond) for value, cond in args
    ):
        return

    values = [
        (expr_val.get_value(value), expr_val.get_value(cond)) for value, cond in args
    ]
    expr_val.set_value(node, sympy.Piecewise(*values))
