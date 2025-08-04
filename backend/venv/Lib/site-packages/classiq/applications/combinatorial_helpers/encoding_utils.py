import math
from itertools import filterfalse
from typing import Any, Union, cast

import numpy as np
import pyomo.environ as pyo
from pyomo.core.base.component import ComponentData, _ComponentBase
from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.base.var import VarData
from pyomo.core.expr.numeric_expr import (
    MonomialTermExpression,
    ProductExpression,
)
from pyomo.core.expr.visitor import clone_expression
from sympy import Expr

from classiq.interface.exceptions import ClassiqCombOptNoSolutionError

from classiq.applications.combinatorial_helpers import pyomo_utils

_INTEGER_TYPES = [pyo.NonNegativeIntegers, pyo.Integers, pyo.PositiveIntegers]


def is_model_encodable(model: pyo.ConcreteModel) -> bool:
    variables = pyomo_utils.extract(model, pyo.Var)
    return not all(is_var_binary(var) for var in variables)


def is_var_binary(var: VarData) -> bool:
    return var.domain == pyo.Binary or (
        var.domain in _INTEGER_TYPES and var.lb == 0 and var.ub == 1
    )


def is_var_span_power_of_2(var: VarData) -> bool:
    var_span = get_var_span(var)
    return math.log2(var_span + 1).is_integer()


ENCODED_SUFFIX = "_encoded"
ONE_HOT_SUFFIX = "_one_hot"
CONSTRAINT_SUFFIX = "_constraint"


def is_obj_encoded(var: _ComponentBase) -> bool:
    return ENCODED_SUFFIX in var.name


def get_var_span(var: VarData) -> int:
    return var.ub - var.lb


def encoded_obj_name(name: str) -> str:
    return name + ENCODED_SUFFIX


def get_encoded_var_index(var: VarData) -> int:
    indexed_var = var.parent_component()
    index = [
        index_temp for index_temp, var_temp in indexed_var.items() if var_temp is var
    ][0]
    return index[1]


def recursively_remove_monomial_expr(obj: Any) -> None:
    # Due to pyomo bug. see: https://github.com/Pyomo/pyomo/issues/2174
    for arg in getattr(obj, "args", []):
        if isinstance(arg, MonomialTermExpression):
            arg.__class__ = ProductExpression
        recursively_remove_monomial_expr(arg)


def encode_expr(
    expr: pyo.Expression, substitution_dict: dict[int, pyo.Expression]
) -> pyo.Expression:
    encoded_expr = clone_expression(expr=expr, substitute=substitution_dict)
    recursively_remove_monomial_expr(encoded_expr)
    return encoded_expr


def encode_constraints(
    model: pyo.ConcreteModel, substitution_dict: dict[int, pyo.Expression]
) -> None:
    all_constraints = pyomo_utils.extract(model, _GeneralConstraintData)
    constraints = filterfalse(is_obj_encoded, all_constraints)

    for constraint in constraints:
        constraint_expression = encode_expr(constraint.expr, substitution_dict)
        if not isinstance(constraint_expression, bool) and not isinstance(
            constraint_expression, np.bool_
        ):
            constraint.set_value(expr=constraint_expression)
            continue

        deal_with_trivial_boolean_constraint(constraint, constraint_expression, model)


def deal_with_trivial_boolean_constraint(
    constraint: _ComponentBase,
    constraint_expression: Union[bool, Expr],
    model: pyo.ConcreteModel,
) -> None:
    # using '==' on purpose since comparing against sympy's True
    if constraint_expression == True:  # noqa: E712
        pyomo_utils.delete_component(model, cast(ComponentData, constraint))
    if constraint_expression == False:  # noqa: E712
        raise ClassiqCombOptNoSolutionError


def encode_objective(
    model: pyo.ConcreteModel, substitution_dict: dict[int, pyo.Expression]
) -> None:
    objective = next(model.component_objects(pyo.Objective))

    encoded_objective = pyo.Objective(
        expr=encode_expr(objective.expr, substitution_dict),
        sense=objective.sense,
    )
    model.del_component(objective.name)
    setattr(
        model,
        objective.name,
        encoded_objective,
    )
