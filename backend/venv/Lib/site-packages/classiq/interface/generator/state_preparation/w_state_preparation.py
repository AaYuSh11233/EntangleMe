import pydantic

from classiq.interface.generator.state_preparation.state_preparation_abc import (
    StatePreparationABC,
)


class WStatePreparation(StatePreparationABC):
    num_qubits: pydantic.PositiveInt = pydantic.Field(default=3)

    @property
    def num_state_qubits(self) -> int:
        return self.num_qubits
