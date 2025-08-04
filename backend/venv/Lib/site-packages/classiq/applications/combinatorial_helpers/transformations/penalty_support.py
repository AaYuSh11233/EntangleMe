from pyomo.core import ConcreteModel
from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.base.var import VarData
from pyomo.core.expr.relational_expr import EqualityExpression

from classiq.applications.combinatorial_helpers import (
    allowed_constraints,
    encoding_utils,
)
from classiq.applications.combinatorial_helpers.pyomo_utils import extract
from classiq.applications.combinatorial_helpers.sympy_utils import sympyify_expression


def is_model_penalty_supported(model: ConcreteModel) -> bool:
    variables = extract(model, VarData)
    is_vars_supported = all(is_var_penalty_supported(var) for var in variables)

    constraints = extract(model, _GeneralConstraintData)
    is_constraints_supported = all(
        is_constraint_penalty_supported(constraint) for constraint in constraints
    )
    return is_vars_supported and is_constraints_supported


def is_var_penalty_supported(var: VarData) -> bool:
    return encoding_utils.is_var_binary(var) or encoding_utils.is_var_span_power_of_2(
        var
    )


def is_constraint_penalty_supported(constraint: _GeneralConstraintData) -> bool:
    if isinstance(constraint.expr, EqualityExpression):
        return True

    sympy_expr = sympyify_expression(constraint.expr)

    return allowed_constraints.is_constraint_sum_less_than_one(sympy_expr)
