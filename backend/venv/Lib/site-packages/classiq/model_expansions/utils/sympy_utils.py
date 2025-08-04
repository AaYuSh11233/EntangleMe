from typing import Any

from sympy import Number


def unwrap_sympy_numeric(n: Any) -> Any:
    if not isinstance(n, Number) or not n.is_constant():
        return n
    if n.is_Integer:
        return int(n)
    return float(n)


def is_constant_subscript(index: Any) -> bool:
    if not isinstance(index, slice):
        return isinstance(unwrap_sympy_numeric(index), int)
    start = unwrap_sympy_numeric(index.start)
    stop = unwrap_sympy_numeric(index.stop)
    step = unwrap_sympy_numeric(index.step)
    return (
        (start is None or isinstance(start, int))
        and (stop is None or isinstance(stop, int))
        and (step is None or isinstance(step, int))
    )
