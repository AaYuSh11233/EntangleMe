import pydantic

from classiq.interface.generator.control_state import ControlState
from classiq.interface.generator.state_preparation.state_preparation_abc import (
    StatePreparationABC,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticNonEmptyString


class ComputationalBasisStatePreparation(StatePreparationABC):
    computational_state: PydanticNonEmptyString = pydantic.Field(
        description="binary computational state to create"
    )

    @pydantic.field_validator("computational_state")
    @classmethod
    def _validate_computational_state(
        cls, computational_state: PydanticNonEmptyString
    ) -> PydanticNonEmptyString:
        ControlState.validate_control_string(computational_state)
        return computational_state

    @property
    def num_state_qubits(self) -> int:
        return len(self.computational_state)

    def get_power_order(self) -> int:
        return 2
