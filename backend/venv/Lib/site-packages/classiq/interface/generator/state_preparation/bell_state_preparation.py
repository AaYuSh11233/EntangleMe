from typing import Literal

import pydantic

from classiq.interface.generator.state_preparation.state_preparation_abc import (
    StatePreparationABC,
)

BellStateName = Literal["psi+", "psi-", "phi+", "phi-"]
_ALIGNED_STATES: frozenset[BellStateName] = frozenset({"phi+", "phi-"})
_SIGNED_STATES: frozenset[BellStateName] = frozenset({"psi-", "phi-"})


class BellStatePreparation(StatePreparationABC):
    name: BellStateName = pydantic.Field(default="phi+")

    @property
    def aligned(self) -> bool:
        return self.name in _ALIGNED_STATES

    @property
    def signed(self) -> bool:
        return self.name in _SIGNED_STATES

    @property
    def num_state_qubits(self) -> int:
        return 2
