import numpy as np
import pyomo.core as pyo


def greater_than_ilp(
    a: np.ndarray, b: np.ndarray, c: np.ndarray, bound: int
) -> pyo.ConcreteModel:
    # model constraint: a*x <= b
    model = pyo.ConcreteModel()
    assert b.ndim == c.ndim == 1

    num_vars = len(c)
    num_constraints = len(b)

    assert a.shape == (num_constraints, num_vars)

    model.x = pyo.Var(
        range(num_vars), domain=pyo.NonNegativeIntegers, bounds=(0, bound)
    )

    @model.Constraint(range(num_constraints))
    def monotone_rule(model: pyo.ConcreteModel, idx: int) -> pyo.ExpressionBase:
        return a[idx, :] @ list(model.x.values()) >= float(b[idx])

    # model objective: max(c * x)
    model.cost = pyo.Objective(expr=c @ list(model.x.values()), sense=pyo.minimize)

    return model
