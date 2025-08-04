from typing import Union, get_args, get_origin

from classiq.qmod.symbolic_expr import SymbolicExpr

SymbolicTypes = Union[SymbolicExpr, int, float, bool, tuple["SymbolicTypes", ...]]
SYMBOLIC_TYPES = tuple(get_origin(t) or t for t in get_args(SymbolicTypes))
