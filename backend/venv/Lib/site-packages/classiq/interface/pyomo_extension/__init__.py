import pyomo.core
import sympy
from pyomo.core.expr.relational_expr import EqualityExpression

from classiq.interface.pyomo_extension import (
    equality_expression,
    inequality_expression,
    pyomo_sympy_bimap,
    set_pprint,
)

pyomo.core.expr.relational_expr.InequalityExpression.getname = (
    inequality_expression.getname
)

pyomo.core.expr.relational_expr.EqualityExpression.getname = equality_expression.getname

pyomo.core.base.set.Set._pprint_members = staticmethod(set_pprint.pprint_members)

pyomo.core.expr.sympy_tools._pyomo_operator_map.update({EqualityExpression: sympy.Eq})

pyomo.core.expr.sympy_tools.PyomoSympyBimap.getSympySymbol = (
    pyomo_sympy_bimap.get_sympy_symbol
)
