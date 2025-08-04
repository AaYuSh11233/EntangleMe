from typing import TYPE_CHECKING, Annotated, Any

import pydantic
from pydantic import StringConstraints
from typing_extensions import Self

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator import function_params
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo

STATE = "state"
TARGET = "target"

LENGTH_ERROR_MESSAGE = "Field required"

if TYPE_CHECKING:
    PydanticPauliBasisStr = str
else:
    PydanticPauliBasisStr = Annotated[
        str,
        StringConstraints(
            to_lower=True,
            pattern=r"[xyz]",
        ),
    ]


class LinearPauliRotations(function_params.FunctionParams):
    """
    Perform independent linear rotations on target qubits, each controlled by an identical
    n-qubit state register |x>.

    Each target qubit, indexed with k and denoted by q_k, undergoes the following transformation:
    |x>|q_k> -> |x> * [cos(theta(x,k)/2) + i*sin(theta(x,k)/2)*sigma]|q_k>
    with sigma being 'X', 'Y' or 'Z' Pauli matrix, and the angle is a linear function of the state,
    theta(x,k)/2 = (slope(k)*x + offset(k))/2.

    For example, a 'Y' rotation on one target qubit will result in a circuit implementing the following logic:
    |x>|0> -> cos((slope*x + offset)/2)|x>|0> + sin((slope*x + offset)/2)|x>|1>

            q_0: ─────────────────────────■───────── ... ──────────────────────
                                          │
                                          .
                                          │
        q_(n-1): ─────────────────────────┼───────── ... ───────────■──────────
                  ┌────────────┐  ┌───────┴───────┐       ┌─────────┴─────────┐
         target: ─┤ RY(offset) ├──┤ RY(2^0 slope) ├  ...  ┤ RY(2^(n-1) slope) ├
                  └────────────┘  └───────────────┘       └───────────────────┘
    """

    num_state_qubits: pydantic.PositiveInt = pydantic.Field(
        description="The number of input qubits"
    )
    bases: list[PydanticPauliBasisStr] = pydantic.Field(
        description="The types of Pauli rotations ('X', 'Y', 'Z')."
    )
    slopes: list[float] = pydantic.Field(
        description="The slopes of the controlled rotations."
    )
    offsets: list[float] = pydantic.Field(
        description="The offsets of the controlled rotations."
    )

    @pydantic.field_validator("bases", "slopes", "offsets", mode="before")
    @classmethod
    def as_list(cls, v: Any) -> list[Any]:
        if not isinstance(v, list):
            v = [v]
        res = []
        for x in v:
            element = x
            if isinstance(x, str):
                res.append(element.lower())
            else:
                res.append(element)
        return res

    @pydantic.model_validator(mode="after")
    def validate_lists(self) -> Self:
        offsets = self.offsets or list()
        bases = self.bases or list()
        slopes = self.slopes or list()
        if len(slopes) == len(offsets) and len(offsets) == len(bases):
            return self
        raise ClassiqValueError(LENGTH_ERROR_MESSAGE)

    def _create_ios(self) -> None:
        self._inputs = {
            STATE: RegisterArithmeticInfo(size=self.num_state_qubits),
            TARGET: RegisterArithmeticInfo(size=len(self.bases)),
        }
        self._outputs = {**self.inputs}
