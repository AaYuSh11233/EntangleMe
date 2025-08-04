import itertools
from typing import Union

import networkx as nx
import pyomo.core as pyo


def tsp_digraph(
    graph: nx.DiGraph, source: Union[int, str], sink: Union[int, str], nonedge: int
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()

    assert source in graph.nodes(), "source node is out of range"
    assert sink in graph.nodes(), "sink node is out of range"

    points = list(graph.nodes() - {source, sink})
    steps = range(1, graph.number_of_nodes() - 1)
    idxs = list(itertools.product(points, steps))
    model.x = pyo.Var(
        idxs, domain=pyo.Binary
    )  # x[i, j] = 1 indicates that point i is visited at step j

    @model.Constraint(points)
    def each_step_visits_one_point_rule(
        model: pyo.ConcreteModel, ii: int
    ) -> pyo.ExpressionBase:
        return sum(model.x[ii, jj] for jj in steps) == 1

    @model.Constraint(steps)
    def each_point_visited_once_rule(
        model: pyo.ConcreteModel, jj: int
    ) -> pyo.ExpressionBase:
        return sum(model.x[ii, jj] for ii in points) == 1

    def is_travel_between_2_points(point1: int, point2: int) -> pyo.ExpressionBase:
        if point1 == source:
            if point2 == sink:
                return 0
            return model.x[point2, steps[0]]

        if point1 == sink:
            return 0

        if point2 == source:
            return 0

        if point2 == sink:
            return model.x[point1, steps[-1]]

        return sum(model.x[point1, kk] * model.x[point2, kk + 1] for kk in steps[:-1])

    model.cost = pyo.Objective(
        expr=sum(
            graph.get_edge_data(point1, point2, default={"weight": nonedge})["weight"]
            * is_travel_between_2_points(point1, point2)
            for point1, point2 in itertools.product(graph.nodes, repeat=2)
            if point1 != point2
        )
    )
    return model
