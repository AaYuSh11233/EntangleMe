import inspect
from typing import Any, NoReturn

import sympy

_SYMPY_MEMBERS = [name for name, _ in inspect.getmembers(sympy.Symbol)] + ["precedence"]


def subscript_to_str(index: Any) -> str:
    if not isinstance(index, slice):
        return str(index)
    expr = ""
    if index.start is not None:
        expr += str(index.start)
    expr += ":"
    if index.stop is not None:
        expr += str(index.stop)
    if index.step is not None:
        expr += f":{index.step}"
    return expr


class AnyClassicalValue(sympy.Symbol):
    def __getitem__(self, item: Any) -> "AnyClassicalValue":
        if isinstance(item, slice):
            return AnyClassicalValue(f"{self}[{subscript_to_str(item)}]")
        return AnyClassicalValue(f"do_subscript({self}, {item})")

    def __getattribute__(self, attr: str) -> Any:
        if attr.startswith("_") or attr in _SYMPY_MEMBERS:
            return super().__getattribute__(attr)
        return AnyClassicalValue(f"get_field({self}, '{attr}')")

    def __len__(self) -> NoReturn:
        raise TypeError("object of type 'AnyClassicalValue' has no len()")

    def __iter__(self) -> NoReturn:
        raise TypeError("'AnyClassicalValue' object is not iterable")

    def __bool__(self) -> bool:
        return True
