import math

import networkx as nx
import pyomo.core as pyo
import pyomo.core.expr.numeric_expr as pyo_expr

Node = int
Edge = tuple[Node, Node]
Pubo = dict[tuple[Edge, ...], float]


def build_mht_pyomo_model(
    pubo: Pubo, scenario_graph: nx.DiGraph, has_constraints: bool = True
) -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.Nodes = pyo.Set(initialize=list(scenario_graph.nodes))
    model.Arcs = pyo.Set(initialize=list(scenario_graph.edges))
    model.x = pyo.Var(model.Arcs, domain=pyo.Binary)

    _decimals = 3

    if has_constraints:

        @model.Constraint(model.Nodes)
        def out_edges_rule(
            model: pyo.ConcreteModel, idx: int
        ) -> pyo_expr.ExpressionBase:
            out_nodes = [
                node_id for node_id in model.Nodes if [idx, node_id] in model.Arcs
            ]
            if len(out_nodes) >= 2:
                return sum(model.x[idx, node_id] for node_id in out_nodes) <= 1
            else:
                return pyo.Constraint.Feasible

        @model.Constraint(model.Nodes)
        def in_edges_rule(
            model: pyo.ConcreteModel, idx: int
        ) -> pyo_expr.ExpressionBase:
            in_nodes = [
                node_id for node_id in model.Nodes if [node_id, idx] in model.Arcs
            ]
            if len(in_nodes) >= 2:
                return sum(model.x[node_id, idx] for node_id in in_nodes) <= 1
            else:
                return pyo.Constraint.Feasible

    def obj_expression(model: pyo.ConcreteModel) -> pyo_expr.ExpressionBase:
        return sum(
            round(pubo_energy, _decimals)
            * math.prod(model.x[edge] for edge in pubo_edges)
            for pubo_edges, pubo_energy in pubo.items()
        )

    model.cost = pyo.Objective(rule=obj_expression, sense=pyo.minimize)

    return model
