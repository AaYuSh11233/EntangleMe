import itertools

from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.expr.relational_expr import EqualityExpression
from pyomo.environ import Expression


def get_penalty_expression(
    flat_constraints: list[_GeneralConstraintData],
) -> Expression:
    return sum(
        _convert_constraint_to_penalty_term(constraint)
        for constraint in flat_constraints
    )


def _convert_constraint_to_penalty_term(
    constraint: _GeneralConstraintData,
) -> Expression:
    if isinstance(constraint.expr, EqualityExpression):
        return (constraint.expr.args[0] - constraint.expr.args[1]) ** 2

    # we can assume that isinstance(constraint.expr, InequalityExpression) and constraint.expr.args[1] == 1
    # due to _is_constraint_penalty_supported method
    else:
        index = 0
        if isinstance(constraint.expr.args[0], int):
            index = 1
        constraint_variables = constraint.expr.args[index].args
        var_pairs = list(itertools.combinations(constraint_variables, 2))
        return sum(var1 * var2 for var1, var2 in var_pairs)
