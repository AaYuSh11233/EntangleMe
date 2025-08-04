import math
from functools import cached_property
from itertools import filterfalse

import pyomo.core as pyo
from pyomo.core.base.component import _ComponentBase
from pyomo.core.expr.sympy_tools import sympy2pyomo_expression, sympyify_expression

from classiq.applications.combinatorial_helpers import pyomo_utils
from classiq.applications.combinatorial_helpers.arithmetic.arithmetic_expression import (
    multivariate_extremum,
)
from classiq.applications.combinatorial_helpers.transformations import penalty_support
from classiq.applications.combinatorial_helpers.transformations.sign_seperation import (
    sign_separation,
)


def slack_vars_convert(model: pyo.ConcreteModel) -> pyo.ConcreteModel:
    constraints = pyomo_utils.extract(model, pyo.Constraint)
    converted_constraints = list(
        filterfalse(penalty_support.is_constraint_penalty_supported, constraints)
    )

    for constraint in converted_constraints:
        convertor = ConstraintConvertor(constraint)
        setattr(model, convertor.slack_var_name, convertor.slack_var)
        setattr(model, convertor.slack_constraint_name, convertor.slack_constraint)

        pyomo_utils.delete_component(model, constraint)

    return model


_SLACK_VAR_SUFFIX = "_slack_var"
_SLACK_SUFFIX = "_slack"


def is_obj_slacked(var: _ComponentBase) -> bool:
    return _SLACK_SUFFIX in var.name


class ConstraintConvertor:
    def __init__(self, constraint: pyo.Constraint) -> None:
        self._symbols_map, self._expr = sympyify_expression(constraint.expr)
        self._expr = sign_separation(self._expr)
        self._expr_lower, self._expr_upper = self._expr.args

        self._name = pyomo_utils.get_name(constraint)

        self.slack_var_name = self._name + _SLACK_VAR_SUFFIX
        self.slack_var_idxs = range(self._bound_int.bit_length())
        self.slack_var = pyo.Var(self.slack_var_idxs, domain=pyo.Binary)
        self.slack_var.construct()

        self.slack_constraint_name = self._name + _SLACK_SUFFIX

    @cached_property
    def _bound_int(self) -> int:
        max_upper = math.ceil(
            multivariate_extremum(self._expr_upper, self._symbols_map, is_min=False)
        )
        min_lower = math.floor(
            multivariate_extremum(self._expr_lower, self._symbols_map, is_min=True)
        )
        return max_upper - min_lower

    @cached_property
    def _slack_coeffs(self) -> list[int]:
        coeffs = [2**idx for idx in self.slack_var_idxs[:-1]]
        coeffs += [self._bound_int - sum(coeffs)]
        return coeffs

    @cached_property
    def _slack_expr(self) -> pyo.Expression:
        return sum(
            coeff * self.slack_var[num] for num, coeff in enumerate(self._slack_coeffs)
        )

    @cached_property
    def slack_constraint(self) -> pyo.Constraint:
        expr_lower_pyomo = sympy2pyomo_expression(self._expr_lower, self._symbols_map)
        expr_upper_pyomo = sympy2pyomo_expression(self._expr_upper, self._symbols_map)

        return pyo.Constraint(
            expr=expr_lower_pyomo + self._slack_expr == expr_upper_pyomo
        )
