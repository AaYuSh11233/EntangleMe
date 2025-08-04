import networkx as nx
import pyomo.core as pyo
import pyomo.core.expr.numeric_expr as pyo_expr


def mis(graph: nx.Graph) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(graph.nodes, domain=pyo.Binary)

    @model.Constraint(graph.edges)
    def independent_rule(
        model: pyo.ConcreteModel, node1: int, node2: int
    ) -> pyo_expr.ExpressionBase:
        return model.x[node1] + model.x[node2] <= 1

    model.cost = pyo.Objective(expr=sum(model.x.values()), sense=pyo.maximize)

    return model
