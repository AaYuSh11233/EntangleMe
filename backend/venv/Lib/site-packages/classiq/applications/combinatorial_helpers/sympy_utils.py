from typing import Optional

import pyomo.core as pyo
from pyomo.core.base.var import VarData
from pyomo.core.expr.sympy_tools import Pyomo2SympyVisitor, PyomoSympyBimap
from sympy import Expr


def sympyify_vars(variables: list[VarData]) -> PyomoSympyBimap:
    symbols_map = PyomoSympyBimap()
    for var in variables:
        Pyomo2SympyVisitor(symbols_map).walk_expression(var)
    return symbols_map


def sympyify_expression(
    expression: pyo.Expression, symbols_map: Optional[PyomoSympyBimap] = None
) -> Expr:
    if symbols_map is None:
        symbols_map = PyomoSympyBimap()

    return Pyomo2SympyVisitor(symbols_map).walk_expression(expression)
