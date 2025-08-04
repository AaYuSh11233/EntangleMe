from itertools import filterfalse

from sympy import (
    Add,
    Expr,
    GreaterThan,
    LessThan,
    Mul,
    Number,
    Symbol,
    expand,
    simplify,
)

from classiq.interface.exceptions import ClassiqCombOptError


def sign_separation(expr: Expr) -> LessThan:
    expr = simplify(expr)
    expr = expand(expr)

    if not isinstance(expr, (LessThan, GreaterThan)):
        raise ClassiqCombOptError("sign separation didn't worked out")

    if isinstance(expr, GreaterThan):
        expr = LessThan(expr.args[1], expr.args[0])

    expr_body = expr.args[0]
    expr_bound = expr.args[1]

    positive_body_args, negative_body_args = _get_positive_and_negative_args(expr_body)

    positive_bound_args, negative_bound_args = _get_positive_and_negative_args(
        expr_bound
    )

    modified_expr = LessThan(
        Add(*positive_body_args) - Add(*negative_bound_args),
        Add(*positive_bound_args) - Add(*negative_body_args),
    )

    return modified_expr


def _get_positive_and_negative_args(expr: Expr) -> tuple[list[Expr], list[Expr]]:
    positive_args = []
    negative_args = []

    if isinstance(expr, Add):
        positive_args += list(filter(_is_positive_expr, expr.args))
        negative_args += list(filterfalse(_is_positive_expr, expr.args))

    elif _is_positive_expr(expr):
        positive_args.append(expr)
    else:
        negative_args.append(expr)

    if not positive_args and not negative_args:
        raise ClassiqCombOptError("sign separation didn't worked out")

    return positive_args, negative_args


def _is_positive_expr(expr: Expr) -> bool:
    return (
        (isinstance(expr, Number) and expr > 0)
        or isinstance(expr, Symbol)
        or (
            isinstance(expr, Mul)
            and isinstance(expr.args[0], Number)
            and expr.args[0] > 0
            and isinstance(expr.args[1], Symbol)
        )
    )
