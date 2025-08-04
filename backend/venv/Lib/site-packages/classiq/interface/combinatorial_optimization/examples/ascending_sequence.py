import numpy as np
import pyomo.core as pyo


def ascending_sequence(coeffs: list[int], bound: int) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(
        range(len(coeffs)), domain=pyo.NonNegativeIntegers, bounds=(0, bound)
    )

    @model.Constraint(range(len(coeffs) - 1))
    def monotone_rule(model: pyo.ConcreteModel, idx: int) -> pyo.ExpressionBase:
        return model.x[idx] <= model.x[idx + 1]

    model.cost = pyo.Objective(
        expr=coeffs @ np.array(list(model.x.values())), sense=pyo.maximize
    )

    return model
