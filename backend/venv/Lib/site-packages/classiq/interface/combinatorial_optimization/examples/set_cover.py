import itertools

import pyomo.core as pyo
import pyomo.core.expr.numeric_expr as pyo_expr


def set_cover(sub_sets: list[list[int]]) -> pyo.ConcreteModel:
    entire_set = set(itertools.chain(*sub_sets))
    n = max(entire_set)
    num_sets = len(sub_sets)
    assert entire_set == set(
        range(1, n + 1)
    ), f"the union of the subsets is {entire_set} not equal to range(1, {n + 1})"

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(num_sets), domain=pyo.Binary)

    @model.Constraint(entire_set)
    def independent_rule(model: pyo.ConcreteModel, num: int) -> pyo_expr.ExpressionBase:
        return sum(model.x[idx] for idx in range(num_sets) if num in sub_sets[idx]) >= 1

    model.cost = pyo.Objective(expr=sum(model.x.values()), sense=pyo.minimize)

    return model
