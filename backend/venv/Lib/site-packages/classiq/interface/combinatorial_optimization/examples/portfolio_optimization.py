import numpy as np
import pyomo.core as pyo


def portfolio_optimization(
    covariances: np.ndarray, returns: np.ndarray, budget: int
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    num_assets = len(returns)
    model.x = pyo.Var(range(num_assets), domain=pyo.Binary)
    x_array = list(model.x.values())

    model.budget = pyo.Constraint(expr=(sum(x_array) == budget))

    risk: float = x_array @ covariances @ x_array
    profit: float = returns @ x_array
    model.risk, model.profit = risk, profit

    model.cost = pyo.Objective(expr=model.risk - model.profit, sense=pyo.minimize)

    return model
