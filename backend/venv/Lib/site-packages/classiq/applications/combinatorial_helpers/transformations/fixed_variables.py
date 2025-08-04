import copy
from typing import Union

from pyomo.core import ConcreteModel, Var
from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.base.var import VarData
from pyomo.core.expr.relational_expr import EqualityExpression
from pyomo.core.expr.visitor import identify_variables

from classiq.interface.exceptions import (
    ClassiqCombOptNoSolutionError,
    ClassiqCombOptTrivialProblemError,
)

from classiq.applications.combinatorial_helpers import (
    encoding_utils,
    pyomo_utils,
    sympy_utils,
)
from classiq.applications.combinatorial_helpers.arithmetic.isolation import isolate
from classiq.applications.combinatorial_helpers.encoding_utils import (
    deal_with_trivial_boolean_constraint,
)
from classiq.applications.combinatorial_helpers.sympy_utils import (
    sympyify_expression,
    sympyify_vars,
)


def remove_fixed_variables(model: ConcreteModel) -> ConcreteModel:
    _should_iterate_fixing = _should_start_fixing(model)

    while _should_iterate_fixing:
        _change_fixing_constraints_to_fixed_value(model)
        variables = pyomo_utils.extract(model, Var)

        substitution_dict = {id(var): _get_value_if_exists(var) for var in variables}

        encoding_utils.encode_constraints(model, substitution_dict)
        encoding_utils.encode_objective(model, substitution_dict)
        _remove_empty_constraints(model)

        _should_iterate_fixing = _should_continue_fixing(model)

    assigned_model = copy.deepcopy(model)
    _check_empty_model(assigned_model)
    _remove_assigned_variables(model)

    return assigned_model


def _should_continue_fixing(model: ConcreteModel) -> bool:
    return bool(len(_get_fixing_constraints(model)))


def _should_start_fixing(model: ConcreteModel) -> bool:
    variables = pyomo_utils.extract(model, Var)
    is_some_var_fixed = any(var.value is not None for var in variables)

    return is_some_var_fixed or _should_continue_fixing(model)


def _change_fixing_constraints_to_fixed_value(model: ConcreteModel) -> None:
    for constraint in _get_fixing_constraints(model):
        var, var_value = _get_var_and_value_from_fixing_constraint(constraint)

        if var.value is not None and var.value != var_value:
            raise ClassiqCombOptNoSolutionError

        if int(var_value) != var_value or var_value < var.lb or var_value > var.ub:
            raise ClassiqCombOptNoSolutionError

        var.fix(int(var_value))
        pyomo_utils.delete_component(model, constraint)


def _get_fixing_constraints(model: ConcreteModel) -> list[_GeneralConstraintData]:
    constraints = pyomo_utils.extract(model, _GeneralConstraintData)
    return list(filter(_is_fixing_constraint, constraints))


def _get_var_and_value_from_fixing_constraint(
    constraint: _GeneralConstraintData,
) -> tuple[VarData, float]:
    var = next(identify_variables(constraint.body))

    if isinstance(constraint.body, VarData):
        return var, constraint.upper.value

    symbols_map = sympyify_vars([var])
    sympy_exp = sympyify_expression(constraint.expr, symbols_map)
    sympy_var = symbols_map.getSympySymbol(var)

    isolated_exp = isolate(sympy_exp, sympy_var)

    return var, float(isolated_exp.args[1])


def _remove_assigned_variables(model: ConcreteModel) -> None:
    for var in pyomo_utils.extract(model, Var):
        if var.value is not None:
            pyomo_utils.delete_component(model, var)


def _remove_empty_constraints(model: ConcreteModel) -> None:
    # (reduces number of slack variables and potential errors)
    for constraint in pyomo_utils.extract(model, _GeneralConstraintData):
        sympyified_expression = sympy_utils.sympyify_expression(constraint.expr)
        deal_with_trivial_boolean_constraint(constraint, sympyified_expression, model)


def add_fixed_variables_to_solution(
    original_model: ConcreteModel, solution: list[int]
) -> list[int]:
    variables = pyomo_utils.extract(original_model, Var)
    solution_iter = iter(solution)
    # var.value might be 0 as well
    solution_with_fixed = []
    for var in variables:
        if var.value is not None:
            solution_with_fixed.append(var.value)
        else:
            solution_with_fixed.append(next(solution_iter, 0))
    solution_with_fixed.extend(list(solution_iter))
    return solution_with_fixed


def _get_value_if_exists(var: VarData) -> Union[int, VarData]:
    return var.value if var.value is not None else var


def _is_fixing_constraint(constraint: _GeneralConstraintData) -> bool:
    return (
        isinstance(constraint.expr, EqualityExpression)
        and len(list(identify_variables(constraint.body))) == 1
    )


def _check_empty_model(model: ConcreteModel) -> None:
    variables = pyomo_utils.extract(model, Var)
    if all(var.value is not None for var in variables):
        solution = add_fixed_variables_to_solution(original_model=model, solution=[])
        raise ClassiqCombOptTrivialProblemError(solution)
