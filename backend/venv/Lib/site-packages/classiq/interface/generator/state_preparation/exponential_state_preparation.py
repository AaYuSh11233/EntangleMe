import pydantic

from classiq.interface.generator.state_preparation.state_preparation_abc import (
    StatePreparationABC,
)


class ExponentialStatePreparation(StatePreparationABC):
    num_qubits: pydantic.PositiveInt = pydantic.Field()
    rate: float = pydantic.Field()

    @property
    def num_state_qubits(self) -> int:
        return self.num_qubits
