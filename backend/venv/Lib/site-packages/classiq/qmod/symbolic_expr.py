from __future__ import annotations

import ast
from enum import Enum as PythonEnum
from typing import Any

import sympy

from classiq.qmod.utilities import qmod_val_to_expr_str


class Symbolic:
    def __init__(self, expr: str, is_quantum: bool) -> None:
        self._expr = expr
        self.is_quantum = is_quantum

    def __str__(self) -> str:
        return self._expr

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self) -> bool:
        try:
            return bool(ast.literal_eval(self._expr))
        except ValueError:
            raise TypeError(
                f"Symbolic expression {self._expr!r} cannot be converted to bool"
            ) from None


class SymbolicExpr(Symbolic):
    def __init__(self, expr: str, is_quantum: bool) -> None:
        super().__init__(expr, is_quantum)

    @staticmethod
    def _binary_op(lhs: Any, rhs: Any, op: str) -> SymbolicExpr:
        if not isinstance(
            lhs, (SymbolicExpr, int, float, bool, PythonEnum, sympy.Basic)
        ):
            raise TypeError(f"Invalid lhs argument {lhs!r} for binary operation {op!r}")

        if not isinstance(
            rhs, (SymbolicExpr, int, float, bool, PythonEnum, sympy.Basic)
        ):
            raise TypeError(f"Invalid lhs argument {rhs!r} for binary operation {op!r}")

        lhs_str = qmod_val_to_expr_str(lhs)
        if not isinstance(lhs, (int, float, bool, PythonEnum)):
            lhs_str = f"({lhs_str})"
        rhs_str = qmod_val_to_expr_str(rhs)
        if not isinstance(rhs, (int, float, bool, PythonEnum)):
            rhs_str = f"({rhs_str})"

        lhs_is_quantum = isinstance(lhs, SymbolicExpr) and lhs.is_quantum
        rhs_is_quantum = isinstance(rhs, SymbolicExpr) and rhs.is_quantum

        return SymbolicExpr(
            f"{lhs_str} {op} {rhs_str}", lhs_is_quantum or rhs_is_quantum
        )

    @staticmethod
    def _unary_op(arg: Any, op: str) -> SymbolicExpr:
        if not isinstance(arg, (SymbolicExpr, int, float, bool)):
            raise TypeError(f"Invalid argument {arg!r} for unary operation {op!r}")

        arg_is_quantum = isinstance(arg, SymbolicExpr) and arg.is_quantum

        return SymbolicExpr(f"{op}({arg})", arg_is_quantum)

    def __add__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "+")

    def __sub__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "-")

    def __mul__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "*")

    def __truediv__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "/")

    def __floordiv__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "//")

    def __mod__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "%")

    def __pow__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "**")

    def __lshift__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "<<")

    def __rshift__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, ">>")

    def __and__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "&")

    def __xor__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "^")

    def __or__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "|")

    def __radd__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "+")

    def __rsub__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "-")

    def __rmul__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "*")

    def __rtruediv__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "/")

    def __rfloordiv__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "//")

    def __rmod__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "%")

    def __rpow__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "**")

    def __rlshift__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "<<")

    def __rrshift__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, ">>")

    def __rand__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "&")

    def __rxor__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "^")

    def __ror__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(other, self, "|")

    def __lt__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "<")

    def __le__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, "<=")

    def __eq__(self, other: Any) -> SymbolicEquality:  # type: ignore[override]
        return SymbolicEquality(self, other)

    def __ne__(self, other: Any) -> SymbolicExpr:  # type: ignore[override]
        return SymbolicExpr._binary_op(self, other, "!=")

    def __gt__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, ">")

    def __ge__(self, other: Any) -> SymbolicExpr:
        return SymbolicExpr._binary_op(self, other, ">=")

    def __neg__(self) -> SymbolicExpr:
        return SymbolicExpr._unary_op(self, "-")

    def __pos__(self) -> SymbolicExpr:
        return SymbolicExpr._unary_op(self, "+")

    def __abs__(self) -> SymbolicExpr:
        return SymbolicExpr._unary_op(self, "abs")

    def __invert__(self) -> SymbolicExpr:
        return SymbolicExpr._unary_op(self, "~")


class SymbolicEquality(SymbolicExpr):
    def __init__(self, lhs: Any, rhs: Any) -> None:
        sym_expr = SymbolicExpr._binary_op(lhs, rhs, "==")
        super().__init__(sym_expr._expr, sym_expr.is_quantum)
        self.lhs = lhs
        self.rhs = rhs


class SymbolicSubscriptAndField(SymbolicExpr):
    def __getattr__(self, item: str) -> SymbolicSubscriptAndField:
        return SymbolicSubscriptAndField(f"{self}.{item}", is_quantum=self.is_quantum)

    def __getitem__(self, item: Any) -> SymbolicExpr:
        if isinstance(item, slice):
            start = item.start
            stop = item.stop
            step = item.step
            item_is_quantum = (
                (isinstance(start, SymbolicExpr) and start.is_quantum)
                or (isinstance(stop, SymbolicExpr) and stop.is_quantum)
                or (isinstance(step, SymbolicExpr) and step.is_quantum)
            )
            start_str = "" if start is None else qmod_val_to_expr_str(start)
            stop_str = "" if stop is None else qmod_val_to_expr_str(stop)
            step_str = "" if step is None else qmod_val_to_expr_str(step)
            item_str = f"{start_str}:{stop_str}:{step_str}"
        else:
            item_is_quantum = isinstance(item, SymbolicExpr) and item.is_quantum
            item_str = qmod_val_to_expr_str(item)
        return SymbolicSubscriptAndField(
            f"{self}[{item_str}]", is_quantum=self.is_quantum or item_is_quantum
        )
