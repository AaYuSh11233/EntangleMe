from typing import Union

import numpy as np
import pyomo.core as pyo

BoundsList = list[Union[tuple[int, int], int]]


def portfolio_optimization_binary(
    covariances: np.ndarray,
    returns: np.ndarray,
    budget: int,
    constraint_type: str = "",
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    num_assets = len(returns)
    model.x = pyo.Var(range(num_assets), domain=pyo.Binary)
    x_array = list(model.x.values())

    if constraint_type == "eq":
        model.budget = pyo.Constraint(expr=(sum(x_array) == budget))
    elif constraint_type == "ineq":
        model.budget = pyo.Constraint(expr=(sum(x_array) <= budget))

    risk: float = x_array @ covariances @ x_array
    profit: float = returns @ x_array
    model.risk, model.profit = risk, profit

    model.cost = pyo.Objective(expr=model.risk - model.profit, sense=pyo.minimize)

    return model


def portfolio_optimization_integer(
    covariances: np.ndarray,
    returns: np.ndarray,
    bounds: BoundsList,
    budget: int = 0,
    constraint_type: str = "",
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    num_assets = len(returns)

    for idx, bound in enumerate(bounds):
        bounds[idx] = bound if isinstance(bound, (tuple, list)) else (0, bound)

    model.x = pyo.Var(
        range(num_assets), domain=pyo.Integers, bounds=lambda _, idx: bounds[idx]
    )

    x_array: np.ndarray = np.array(list(model.x.values()))

    if constraint_type == "eq":
        model.budget = pyo.Constraint(expr=(sum(x_array) == budget))
    elif constraint_type == "ineq":
        model.budget = pyo.Constraint(expr=(sum(x_array) <= budget))

    risk: float = x_array @ covariances @ x_array
    profit: float = returns @ x_array
    model.risk, model.profit = risk, profit

    model.cost = pyo.Objective(expr=model.risk - model.profit, sense=pyo.minimize)

    return model
