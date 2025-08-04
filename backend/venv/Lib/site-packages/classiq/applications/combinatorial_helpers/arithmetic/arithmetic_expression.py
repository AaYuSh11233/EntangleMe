from typing import Any

import sympy
from pyomo.core.expr.sympy_tools import PyomoSympyBimap
from scipy.optimize import differential_evolution
from sympy import Expr

from classiq.applications.combinatorial_helpers import encoding_utils


def sympy_lambdify(*args: Any, **kwargs: Any) -> Any:
    new_kwargs = kwargs
    new_kwargs["modules"] = ["sympy"]
    return sympy.lambdify(*args, **new_kwargs)


def multivariate_extremum(
    expr: Expr, symbols_map: PyomoSympyBimap, is_min: bool
) -> float:
    if expr.is_number:
        return float(expr)

    free_symbols = tuple(expr.free_symbols)
    bounds = [
        (0, encoding_utils.get_var_span(symbols_map.sympy2pyomo[sym]))
        for sym in free_symbols
    ]

    # differential_evolution finds the global minimum, where we looking for the minimum or the maximum
    extremum_type_coeff = 1 if is_min else -1

    # Should be used only with sanitized imports due to use could be a potential risk to exec function https://docs.sympy.org/latest/modules/utilities/lambdify.html
    func = sympy_lambdify([free_symbols], expr=extremum_type_coeff * expr)
    result = differential_evolution(func, bounds)
    return result.fun * extremum_type_coeff
