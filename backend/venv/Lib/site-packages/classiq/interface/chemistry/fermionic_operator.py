from __future__ import annotations

import itertools
from typing import Union

import numpy as np
import pydantic
from pydantic import ConfigDict

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)

LadderOperator = tuple[str, int]
FermionicOperatorTuple = tuple["FermionicOperator", float]

_SUBSCRIPT_UNICODE_CHARS = {
    "0": "\u2080",
    "1": "\u2081",
    "2": "\u2082",
    "3": "\u2083",
    "4": "\u2084",
    "5": "\u2085",
    "6": "\u2086",
    "7": "\u2087",
    "8": "\u2088",
    "9": "\u2089",
}
_SUPERSCRIPT_PLUS = "\u207a"


class FermionicOperator(HashablePydanticBaseModel):
    """
    Specification of a Fermionic operator.
    Input:
    List of ladder operators, each ladder operator is described by a tuple of its
    index and a character indicating if it's a creation ('+') or annihilation operator ('-').
    """

    op_list: list = pydantic.Field(
        description=(
            "A list of tuples each containing an index and a character; for "
            "example [('+', 0), ('-', 1)]."
        ),
    )

    @staticmethod
    def _validate_single_op(op: tuple) -> LadderOperator:
        if not isinstance(op, tuple):
            try:  # type: ignore[unreachable] # it is reachable...
                op = tuple(op)
            except Exception as exc:
                raise ClassiqValueError("Ladder operator should be a tuple.") from exc
        if len(op) != 2:
            raise ClassiqValueError(
                "Ladder operator tuple should be of length two; for example ('+', 1)."
            )

        op_symbol = op[0]
        if op_symbol == "LadderOperator.PLUS":
            op_symbol = "+"
        elif op_symbol == "LadderOperator.MINUS":
            op_symbol = "-"
        if op_symbol not in ("+", "-"):
            raise ClassiqValueError(
                f"The first term in a ladder operator tuple indicates if its a raising "
                f"(LadderOperator.PLUS / '+') or lowering (LadderOperator.MINUS / '-') "
                f"operator. Received {op_symbol}"
            )
        op_index = op[1]
        if not isinstance(op_index, int):
            raise ClassiqValueError(
                "The second term in a ladder operator tuple indicates its index and should be of type int"
            )

        return (op_symbol, op_index)

    @pydantic.field_validator("op_list")
    @classmethod
    def _validate_op_list(cls, op_list: list) -> list:
        return list(map(cls._validate_single_op, op_list))

    def __mul__(self, coeff: Union[float, int]) -> SummedFermionicOperator:
        if isinstance(coeff, (float, int)):
            return SummedFermionicOperator(op_list=[(self, float(coeff))])
        raise ClassiqValueError(
            "The coefficient multiplying Fermionic Operator should be of type float"
        )

    __rmul__ = __mul__

    def __add__(
        self, other: Union[SummedFermionicOperator, FermionicOperator]
    ) -> SummedFermionicOperator:
        if isinstance(other, SummedFermionicOperator):
            return SummedFermionicOperator(op_list=[(self, 1.0)] + other.op_list)
        elif isinstance(other, FermionicOperator):
            return SummedFermionicOperator(op_list=[(self, 1.0)] + [(other, 1.0)])
        raise ClassiqValueError(
            "FermionicOperator can be summed together only with type FermionicOperator or SummedFermionicOperator"
        )

    model_config = ConfigDict(frozen=True)

    @staticmethod
    def _to_ladder_op(char: str) -> str:
        return "a" + _SUPERSCRIPT_PLUS if char == "+" else "a"

    @staticmethod
    def _to_subscript(num: int) -> str:
        return "".join(_SUBSCRIPT_UNICODE_CHARS[digit] for digit in str(num))

    def __str__(self) -> str:
        return "".join(
            f"{self._to_ladder_op(char)}{self._to_subscript(index)}"
            for (char, index) in self.op_list
        )

    @property
    def all_indices(self) -> set[int]:
        return {op[1] for op in self.op_list}


class SummedFermionicOperator(HashablePydanticBaseModel):
    """
    Specification of a summed Fermionic operator.
    Input:
    List of fermionic operators tuples, The first term in the tuple is the FermionicOperator and the second term is its coefficient.
    For example:
    op1 = FermionicOperator(op_list=[('+', 0), ('-', 1)])
    op2 = FermionicOperator(op_list=[('-', 0), ('-', 1)])
    summed_operator = SummedFermionicOperator(op_list=[(op1, 0.2), (op2, 6.7)])
    """

    op_list: list = pydantic.Field(
        description="A list of tuples each containing a FermionicOperator and a coefficient.",
    )
    model_config = ConfigDict(frozen=True)

    @staticmethod
    def _validate_single_op(op: tuple) -> FermionicOperatorTuple:
        # is it tuple - if not, convert to tuple
        if not isinstance(op, tuple):
            try:  # type: ignore[unreachable] # it is reachable...
                op = tuple(op)
            except Exception as exc:
                raise ClassiqValueError("Operator should be a tuple.") from exc
        if len(op) != 2:
            raise ClassiqValueError("Operator tuple should be of length two.")

        # is it FermionicOperator - if not, convert to FermionicOperator
        if not isinstance(op[0], FermionicOperator):
            try:
                op = (FermionicOperator(**op[0]), op[1])
            except Exception as exc:
                raise ClassiqValueError(
                    "The first term in the operator tuple should be an instance of the FermionicOperator class"
                ) from exc

        if not isinstance(op[1], float):
            raise ClassiqValueError(
                "The second term in the operator tuple indicates its coefficient and should be of type float"
            )

        return op  # type: ignore[return-value] # mypy thinks that it is `Tuple[Any, ...]`, though the asserts here tell otherwise..

    @pydantic.field_validator("op_list")
    @classmethod
    def _validate_op_list(cls, op_list: list) -> list:
        return list(map(cls._validate_single_op, op_list))

    def __add__(
        self, other: Union[SummedFermionicOperator, FermionicOperator]
    ) -> SummedFermionicOperator:
        if isinstance(other, SummedFermionicOperator):
            return SummedFermionicOperator(op_list=self.op_list + other.op_list)
        elif isinstance(other, FermionicOperator):
            return SummedFermionicOperator(op_list=self.op_list + [(other, 1.0)])
        raise ClassiqValueError(
            "FermionicOperator can be summed together only with type FermionicOperator or SummedFermionicOperator"
        )

    def is_close(self, other: SummedFermionicOperator) -> bool:
        if not isinstance(other, SummedFermionicOperator):
            return False  # type: ignore[unreachable]

        if len(self.op_list) != len(other.op_list):
            return False

        for (op1, coeff1), (op2, coeff2) in zip(self.op_list, other.op_list):
            if op1 != op2 or not np.isclose(coeff1, coeff2):
                return False

        return True

    @property
    def _all_indices(self) -> set[int]:
        return set(
            itertools.chain.from_iterable(op.all_indices for op, _ in self.op_list)
        )

    @property
    def num_qubits(self) -> int:
        return len(self._all_indices)

    def __str__(self) -> str:
        return " + \n".join(str(op[1]) + " * " + str(op[0]) for op in self.op_list)
