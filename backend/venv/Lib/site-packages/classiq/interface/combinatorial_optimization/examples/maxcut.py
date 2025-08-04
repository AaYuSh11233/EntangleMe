import networkx as nx
import pyomo.core as pyo


def arithmetic_eq(x1: int, x2: int) -> int:
    return x1 * x2 + (1 - x1) * (1 - x2)


def maxcut(graph: nx.Graph) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(graph.nodes, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(
            arithmetic_eq(model.x[node1], model.x[node2])
            for (node1, node2) in graph.edges
        ),
        sense=pyo.minimize,
    )

    return model
