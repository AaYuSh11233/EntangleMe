import itertools

import numpy as np
import pyomo.core as pyo
import pyomo.core.expr.numeric_expr as pyo_expr


def tsp(distance_matrix: np.ndarray) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()

    assert (
        distance_matrix.shape[0] == distance_matrix.shape[1]
    ), "distance_matrix is not square"

    num_points = distance_matrix.shape[0]

    points = range(num_points)
    idxs = list(itertools.product(points, repeat=2))
    model.x = pyo.Var(
        idxs, domain=pyo.Binary
    )  # x[i, j] = 1 indicates that point i is visited at step j

    @model.Constraint(points)
    def each_step_visits_one_point_rule(
        model: pyo.ConcreteModel, ii: int
    ) -> pyo_expr.ExpressionBase:
        return sum(model.x[ii, jj] for jj in range(num_points)) == 1

    @model.Constraint(points)
    def each_point_visited_once_rule(
        model: pyo.ConcreteModel, jj: int
    ) -> pyo_expr.ExpressionBase:
        return sum(model.x[ii, jj] for ii in range(num_points)) == 1

    def is_travel_between_2_points(point1: int, point2: int) -> pyo_expr.ExpressionBase:
        return sum(model.x[point1, kk] * model.x[point2, kk + 1] for kk in points[:-1])

    model.cost = pyo.Objective(
        expr=sum(
            distance_matrix[point1, point2] * is_travel_between_2_points(point1, point2)
            for point1, point2 in idxs
        )
    )

    return model
