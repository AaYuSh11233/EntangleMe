import pyomo.environ as pyo


def is_maximization(model: pyo.ConcreteModel) -> bool:
    objectives = list(model.component_objects(pyo.Objective))
    assert len(objectives) == 1, "supports only a single objective"
    return objectives[0].sense == pyo.maximize
