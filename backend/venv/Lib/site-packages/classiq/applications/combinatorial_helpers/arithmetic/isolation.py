from sympy import Eq, Expr, GreaterThan, LessThan, Rational, Symbol, solve
from sympy.core.relational import Relational

from classiq.interface.exceptions import ClassiqCombOptNoSolutionError


def isolate(expression: Expr, var: Symbol) -> Expr:
    isolated_exp = solve(expression, var)
    # This converts Rationals to Floats which is needed since we don't support division in arithmetic
    if isinstance(isolated_exp, Relational) and _has_rational_atom(isolated_exp):
        isolated_exp = isolated_exp.evalf()

    if isinstance(expression, Eq):
        if len(isolated_exp) == 1:
            isolated_exp = type(expression)(var, isolated_exp[0])
        elif len(isolated_exp) > 1:
            # sympy didn't manage to isolate an expression
            isolated_exp = expression
        else:
            raise ClassiqCombOptNoSolutionError

    else:
        if _is_symbol_in_right_hand_side(isolated_exp):
            isolated_exp = _reverse_ineq_exp(isolated_exp)

    return isolated_exp


def _has_rational_atom(expression: Relational) -> bool:
    return any(type(atom) is Rational for atom in expression.atoms())


def _is_symbol_in_right_hand_side(expression: Expr) -> bool:
    return isinstance(expression.args[1], Symbol) and not isinstance(
        expression.args[0], Symbol
    )


def _reverse_ineq_exp(expression: Expr) -> Expr:
    original_relation = type(expression)
    reverse_relation = LessThan if original_relation is GreaterThan else GreaterThan
    return reverse_relation(expression.args[1], expression.args[0])
