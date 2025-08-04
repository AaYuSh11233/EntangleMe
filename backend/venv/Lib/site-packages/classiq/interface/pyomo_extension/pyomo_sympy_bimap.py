from typing import Any

import sympy
from pyomo.core.base.var import VarData
from pyomo.core.expr.sympy_tools import PyomoSympyBimap


# This code is a pure copy paste from pyomo.core.expr.sympy_tools.PyomoSympyBimap.getSympySymbol
# except one line.
def get_sympy_symbol(self: PyomoSympyBimap, pyomo_object: Any) -> sympy.Symbol:
    if pyomo_object in self.pyomo2sympy:
        return self.pyomo2sympy[pyomo_object]
    # Pyomo currently ONLY supports Real variables (not complex
    # variables).  If that ever changes, then we will need to
    # revisit hard-coding the symbol type here
    # Here is the difference from the original code
    sympy_obj = sympy.Symbol(_get_sympy_name(pyomo_object), real=True)
    self.i += 1
    self.pyomo2sympy[pyomo_object] = sympy_obj
    self.sympy2pyomo[sympy_obj] = pyomo_object
    return sympy_obj


# This is the difference from the original function.
# The name for the new sympy object is derived
# from the pyomo object, instead of using generic name with serial number.
# This is intended to have better corelation between the the pyomo variables and sympy variables.
def _get_sympy_name(pyomo_object: VarData) -> str:
    return pyomo_object.name.replace("[", "").replace("]", "")
