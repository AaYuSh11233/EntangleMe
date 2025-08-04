import pydantic
from typing_extensions import Self

from classiq.interface.exceptions import ClassiqStateInitializationError
from classiq.interface.generator.arith import number_utils

_NON_INTEGER_INITIALIZATION_ERROR_MSG: str = (
    "Only natural numbers are supported as initial conditions"
)


class RegisterInitialization(pydantic.BaseModel):
    name: str
    qubits: list[int]
    initial_condition: pydantic.NonNegativeInt

    @pydantic.field_validator("initial_condition", mode="before")
    @classmethod
    def _validate_initial_condition(cls, value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise ClassiqStateInitializationError(_NON_INTEGER_INITIALIZATION_ERROR_MSG)
        return value

    @pydantic.model_validator(mode="after")
    def _validate_register_initialization(self) -> Self:
        qubits: list[int] = self.qubits or []
        initial_condition: int = self.initial_condition or 0
        name: str = self.name or ""

        initial_condition_length = number_utils.size(initial_condition)
        register_length = len(qubits)
        if initial_condition_length > register_length:
            raise ClassiqStateInitializationError(
                f"Register {name} has {register_length} qubits, which is not enough to represent the number {initial_condition}."
            )
        return self
