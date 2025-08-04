import networkx as nx
import pyomo.core as pyo
import pyomo.core.expr.numeric_expr as pyo_expr


def mvc(graph: nx.Graph, k: int) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(graph.nodes, domain=pyo.Binary)
    model.amount_constraint = pyo.Constraint(expr=sum(model.x.values()) == k)

    def obj_expression(model: pyo.ConcreteModel) -> pyo_expr.ExpressionBase:
        # number of edges not covered
        return sum((1 - model.x[i]) * (1 - model.x[j]) for i, j in graph.edges)

    model.cost = pyo.Objective(rule=obj_expression, sense=pyo.minimize)

    return model
