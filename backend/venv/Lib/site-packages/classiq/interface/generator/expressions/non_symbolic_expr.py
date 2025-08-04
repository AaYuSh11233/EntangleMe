from __future__ import annotations

from typing import Any, NoReturn

from classiq.interface.exceptions import ClassiqArithmeticError


class NonSymbolicExpr:
    @property
    def type_name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def _raise_error(type_name: str, op: str) -> NoReturn:
        raise ClassiqArithmeticError(
            f"Unsupported operand type for {op!r}: {type_name}"
        )

    def __add__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "+")

    def __sub__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "-")

    def __mul__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "*")

    def __truediv__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "/")

    def __floordiv__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "//")

    def __mod__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "%")

    def __pow__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "**")

    def __lshift__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "<<")

    def __rshift__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, ">>")

    def __and__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "&")

    def __xor__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "^")

    def __or__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "|")

    def __radd__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "+")

    def __rsub__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "-")

    def __rmul__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "*")

    def __rtruediv__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "/")

    def __rfloordiv__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "//")

    def __rmod__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "%")

    def __rpow__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "**")

    def __rlshift__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "<<")

    def __rrshift__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, ">>")

    def __rand__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "&")

    def __rxor__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "^")

    def __ror__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "|")

    def __lt__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "<")

    def __le__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "<=")

    def __eq__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "==")

    def __ne__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "!=")

    def __gt__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, ">")

    def __ge__(self, other: Any) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, ">=")

    def __neg__(self) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "-")

    def __pos__(self) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "+")

    def __abs__(self) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "abs")

    def __invert__(self) -> NoReturn:
        NonSymbolicExpr._raise_error(self.type_name, "~")
