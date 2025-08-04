import copy
import math
import re
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from functools import reduce
from operator import mul
from types import CodeType
from typing import Any, Optional, TypeVar, Union

import pydantic
import pyomo.core.expr.numeric_expr as pyo_expr
import pyomo.environ as pyo
import sympy
from pyomo.core import ConcreteModel, Constraint, Objective, Var, maximize
from pyomo.core.base.component import ComponentData
from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.base.indexed_component import IndexedComponent
from pyomo.core.base.objective import ScalarObjective
from pyomo.core.base.var import VarData
from pyomo.core.expr.base import ExpressionBase
from pyomo.core.expr.sympy_tools import (
    Pyomo2SympyVisitor,
    PyomoSympyBimap,
    Sympy2PyomoVisitor,
)

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import Integer
from classiq.interface.generator.types.struct_declaration import StructDeclaration

from classiq.qmod.qmod_variable import QArray, QBit, QNum, QStruct, QVar
from classiq.qmod.symbolic_expr import SymbolicExpr

ListVars = list[VarData]
SUPPORTED_TYPES = [
    pyo.Binary,
    pyo.Integers,
    pyo.NegativeIntegers,
    pyo.NonNegativeIntegers,
    pyo.NonPositiveIntegers,
    pyo.PositiveIntegers,
]


class ObjectiveType(Enum):
    Min = "Min"
    Max = "Max"


class CombinatorialOptimizationStructDeclaration(StructDeclaration):
    variable_lower_bound: int = pydantic.Field(default=0)
    variable_upper_bound: int = pydantic.Field(default=1)
    constraints: list[Expression] = pydantic.Field(
        default_factory=list, description="List of constraint expressions"
    )
    objective_type: ObjectiveType = pydantic.Field(
        description="Specify whether the optimization problem is Min or Max"
    )
    objective_function: Expression = pydantic.Field(
        description="The expression to optimize, according to the objective type"
    )


def contains(var_data: VarData, vars_data: ListVars) -> bool:
    # HACK: standard "__containts__ (in)" method doesn't work, because pyomo overrode the __eq__ method (IMO)
    return any(var_data is var_data_temp for var_data_temp in vars_data)


def remove(var_data: VarData, vars_data: ListVars) -> ListVars:
    # HACK: standard "list method remove" method doesn't work, because pyomo overrode the __eq__ method (IMO)
    assert contains(var_data, vars_data), "var not in list"
    vars_data = vars_data.copy()
    for idx, var_data_temp in enumerate(vars_data):
        if var_data_temp is var_data:
            del vars_data[idx]
            break
    return vars_data


def index(var_data: VarData, vars_data: ListVars) -> int:
    # HACK: standard "index method" doesn't work.
    assert contains(var_data, vars_data), "var not in list"
    idxs = [
        idx for idx, var_data_temp in enumerate(vars_data) if var_data is var_data_temp
    ]
    return idxs[0]


T = TypeVar("T")


def extract(model: ConcreteModel, type_: type[T]) -> list[T]:
    if type_ == VarData:
        type_ = Var

    elif type_ == _GeneralConstraintData:
        type_ = Constraint

    components = model.component_objects(type_)
    return [
        component[component_idx]
        for component in components
        for component_idx in component
    ]


def delete_component(model: ConcreteModel, component: ComponentData) -> None:
    parent_ref = component._component

    if parent_ref is None:
        return

    parent_component = parent_ref()

    if component is parent_component:
        model.del_component(component)
    else:
        _delete_element_by_value(parent_component, component)

        if not parent_component:
            model.del_component(parent_component)


def _delete_element_by_value(dict_: dict, value: Any) -> None:
    iter_dict = {**dict_}
    for k, v in iter_dict.items():
        if v is value and k in dict_:
            del dict_[k]


def get_name(component: Union[IndexedComponent, ComponentData]) -> str:
    if isinstance(component, IndexedComponent):
        return component._name  # constraint.name returns "'{name}'"
    else:
        return component.name


class FixedSympy2PyomoVisitor(Sympy2PyomoVisitor):
    def beforeChild(  # noqa: N802
        self, node: Optional[sympy.Expr], child: sympy.Expr, child_idx: Optional[int]
    ) -> tuple[bool, Union[int, float, None]]:
        if not child._args:
            item = self.object_map.getPyomoSymbol(child, None)
            if item is None:
                if isinstance(child, sympy.Integer):  # addition to base implementation
                    item = int(child.evalf())
                else:
                    item = float(child.evalf())
            return False, item
        return True, None


def sympy2pyomo_expression(
    expr: sympy.core.Basic, object_map: PyomoSympyBimap
) -> pyo_expr.ExpressionBase:
    return FixedSympy2PyomoVisitor(object_map).walk_expression(expr)


def convert_pyomo_to_global_presentation(
    pyo_model: pyo.ConcreteModel,
) -> pyo.ConcreteModel:
    problem_struct = pyomo2qmod("nativePyoModel", pyo_model)

    pyomo_model = pyo.ConcreteModel()

    var_names = list(problem_struct.variables.keys())
    pyomo_model.var_set = pyo.Var(
        var_names,
        domain=pyo.NonNegativeIntegers,
        bounds=(
            problem_struct.variable_lower_bound,
            problem_struct.variable_upper_bound,
        ),
    )
    obj_map = PyomoSympyBimap()
    var_dict = {
        var_name: obj_map.getSympySymbol(pyomo_model.var_set[var_name])
        for var_name in var_names
    }

    def expr2pyomo(expr: Expression) -> pyo_expr.ExpressionBase:
        sp_expr = sympy.sympify(expr.expr, locals=var_dict)
        if isinstance(sp_expr, sympy.core.relational.Equality):
            return sympy2pyomo_expression(
                sp_expr.args[0], obj_map
            ) == sympy2pyomo_expression(sp_expr.args[1], obj_map)

        # Note that strict greater/less than are not supported by Pyomo
        return sympy2pyomo_expression(sp_expr, obj_map)

    pyomo_model.constraints = pyo.Constraint(
        pyo.RangeSet(0, len(problem_struct.constraints) - 1),
        rule=lambda model, i: expr2pyomo(problem_struct.constraints[i]),
    )
    pyomo_model.objective = pyo.Objective(
        expr=expr2pyomo(problem_struct.objective_function),
        sense=(
            pyo.maximize
            if problem_struct.objective_type == ObjectiveType.Max
            else pyo.minimize
        ),
    )

    return pyomo_model


def pyomo2qmod(
    struct_name: str, pyo_model: ConcreteModel
) -> CombinatorialOptimizationStructDeclaration:
    pyo_model = copy.deepcopy(pyo_model)
    symbols_map = PyomoSympyBimap()

    variables: list[sympy.Symbol] = []

    bounds_set = False
    lower_bound = None
    upper_bound = None

    for var_dict in pyo_model.component_objects(Var):
        for key in var_dict:
            var = Pyomo2SympyVisitor(symbols_map).walk_expression(var_dict[key])
            var.name = var.name.replace(",", "_")
            variables.append(var)
            if bounds_set:
                if lower_bound != var_dict[key].lb:
                    raise ClassiqValueError(
                        "All problem variables must agree on lower bound"
                    )
                if upper_bound != var_dict[key].ub:
                    raise ClassiqValueError(
                        "All problem variables must agree on upper bound"
                    )
            else:
                lower_bound = var_dict[key].lb
                upper_bound = var_dict[key].ub
                bounds_set = True

    constraint_exprs: list[sympy.Expr] = []

    constraint_exprs.extend(
        Pyomo2SympyVisitor(symbols_map).walk_expression(constraint_dict[key].expr)
        for constraint_dict in pyo_model.component_objects(Constraint)
        for key in constraint_dict
    )

    pyo_objective: ScalarObjective = next(pyo_model.component_objects(Objective))
    objective_type_str = "Max" if pyo_objective.sense == maximize else "Min"
    objective_expr: sympy.Expr = Pyomo2SympyVisitor(symbols_map).walk_expression(
        pyo_objective
    )

    return CombinatorialOptimizationStructDeclaration(
        name=struct_name,
        variables={str(variable): Integer() for variable in variables},
        variable_lower_bound=lower_bound,
        variable_upper_bound=upper_bound,
        constraints=[
            Expression(expr=str(constraint_expr))
            for constraint_expr in constraint_exprs
        ],
        objective_type=objective_type_str,
        objective_function=Expression(expr=str(objective_expr)),
    )


def pyomo_to_qmod_qstruct(struct_name: str, vars: list[VarData]) -> type[QStruct]:
    qmod_struct = type(struct_name, (QStruct,), {})
    qmod_struct.__annotations__ = _get_qstruct_fields(vars)
    return qmod_struct


def _get_qstruct_fields(vars: list[VarData]) -> dict[str, type[QVar]]:
    array_type_sizes = _get_array_sizes(vars)
    fields: dict[str, type[QVar]] = {}
    for var in vars:
        _add_qmod_field(var, array_type_sizes, fields)
    return fields


def _get_array_sizes(vars: list[VarData]) -> dict[str, tuple[int, ...]]:
    array_types: dict[str, set[tuple]] = defaultdict(set)
    for var in vars:
        if is_index_var(var):
            array_types[get_field_name(var.parent_component())].add(
                index_as_tuple(var.index())
            )
    return {
        name: dimensions
        for name, indices in array_types.items()
        if (dimensions := _get_indices_dimensions(indices, strict=False)) is not None
    }


def _get_indices_dimensions(
    indices: set[tuple[int, ...]], *, strict: bool
) -> Optional[tuple[int, ...]]:
    indices_list = list(indices)
    if len(indices) == 0:
        return None
    first_idx = indices_list[0]
    if len(first_idx) == 0:
        return None
    if any(len(idx) != len(first_idx) for idx in indices_list[1:]):
        return None
    dimension_bounds = [(idx, idx) for idx in first_idx]
    for multi_idx in indices_list[1:]:
        for dim_idx, idx in enumerate(multi_idx):
            dimension_bounds[dim_idx] = (
                min(dimension_bounds[dim_idx][0], idx),
                max(dimension_bounds[dim_idx][1], idx),
            )
    if strict and any(lb != 0 for lb, ub in dimension_bounds):
        return None
    dimensions = tuple(ub + 1 for _, ub in dimension_bounds)
    if strict and reduce(mul, dimensions) != len(indices_list):
        return None
    return dimensions


def _add_qmod_field(
    var: VarData,
    array_type_sizes: dict[str, tuple[int, ...]],
    fields: dict[str, type[QVar]],
) -> None:
    parent_name = get_field_name(var.parent_component())
    if parent_name not in array_type_sizes:
        var_name = get_field_name(var)
        fields[var_name] = _get_qmod_field_type(var_name, var)
        return
    if parent_name in fields:
        return
    dimensions = array_type_sizes[parent_name]
    qmod_type: type[QVar] = _get_qmod_field_type(parent_name, var)
    for dim in reversed(dimensions):
        qmod_type = QArray[qmod_type, dim]  # type:ignore[valid-type]
    fields[parent_name] = qmod_type


def _get_qmod_field_type(var_name: str, var_data: VarData) -> type[QVar]:
    if var_data.domain not in SUPPORTED_TYPES:
        raise ClassiqValueError(
            f"Type {str(var_data.domain)!r} of variable {var_name!r} is not supported"
        )

    if var_data.domain == pyo.Binary:
        return QBit

    bounds = var_data.bounds
    if bounds is None:
        raise ClassiqValueError(f"Variable {var_name!r} has no bounds")
    lb, ub = bounds
    if not isinstance(lb, int) or not isinstance(ub, int):
        raise ClassiqValueError(
            f"Non-integer bounds for variable {var_name!r} are not supported"
        )
    qnum: Any = QNum  # mypy shenanigans
    return qnum[math.ceil(math.log2(ub - lb + 1)), False, 0]


def evaluate_objective(
    var_mapping: dict[Any, Union[str, tuple[str, tuple[int, ...]]]],
    sympy_expr: sympy.Expr,
    code_expr: CodeType,
    struct_obj: Any,
) -> Any:
    sympy_assignment = {
        sympy_var: (
            getattr(struct_obj, field_accessor)
            if isinstance(field_accessor, str)
            else _get_item(getattr(struct_obj, field_accessor[0]), field_accessor[1])
        )
        for sympy_var, field_accessor in var_mapping.items()
    }

    # classical objective evaluation
    if not isinstance(struct_obj, QStruct):
        var_assignment = {
            str(sympy_var): value for sympy_var, value in sympy_assignment.items()
        }
        return eval(code_expr, {}, var_assignment)  # noqa: S307

    # quantum objective evaluation
    expr_str = str(sympy_expr).replace("'", "")
    for var_name, var_value in sympy_assignment.items():
        var_name = str(var_name).replace("'", "")
        expr_str = re.sub(rf"\b{var_name}\b", str(var_value), expr_str)
    return SymbolicExpr(expr=expr_str, is_quantum=True)


def _get_item(obj: Any, multi_index: tuple[int, ...]) -> Any:
    for idx in multi_index:
        obj = obj[idx]
    return obj


def get_field_name(var: VarData) -> str:
    return var.local_name.replace("[", "_").replace("]", "").replace(",", "_")


def is_index_var(var: VarData) -> bool:
    index = var.index()
    return isinstance(index, int) or (
        isinstance(index, tuple) and all(isinstance(idx, int) for idx in index)
    )


def index_as_tuple(index: Union[int, tuple[int, ...]]) -> tuple[int, ...]:
    if isinstance(index, int):
        return (index,)
    return index


@contextmanager
def add_var_domain_constraints(model: ConcreteModel) -> Iterator[None]:
    vars = extract(model, VarData)
    constraints = [
        constraint
        for var in vars
        if (constraint := _get_var_domain_constraint(var)) is not None
    ]
    if len(constraints) == 0:
        yield
        return
    model.var_domain_constraints = pyo.ConstraintList()
    for constraint in constraints:
        model.var_domain_constraints.add(constraint)
    yield
    model.del_component("var_domain_constraints")


def _get_var_domain_constraint(var: VarData) -> Optional[ExpressionBase]:
    bounds = var.bounds
    if (
        type(bounds) is not tuple
        or len(bounds) != 2
        or not all(isinstance(bounds[idx], int) for idx in (0, 1))
    ):
        raise ClassiqValueError(
            f"Missing bounds for variable {var.local_name}. Expected both lower and "
            f"upper bounds, got {bounds}"
        )
    lb, ub = bounds
    if ub < lb:
        raise ClassiqValueError(
            f"Illegal bounds for variable {var.local_name}. The upper bound ({ub}) is "
            f"lesser than the lower bound ({lb})"
        )
    ub_norm = ub - lb + 1
    if ub_norm & (ub_norm - 1) == 0:
        return None
    return var <= ub
