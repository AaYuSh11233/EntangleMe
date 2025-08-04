import pydantic

from classiq.interface.generator.state_preparation.state_preparation_abc import (
    StatePreparationABC,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticLargerThanOneInteger


class GHZStatePreparation(StatePreparationABC):
    num_qubits: PydanticLargerThanOneInteger = pydantic.Field(default=3)

    @property
    def num_state_qubits(self) -> int:
        return self.num_qubits
