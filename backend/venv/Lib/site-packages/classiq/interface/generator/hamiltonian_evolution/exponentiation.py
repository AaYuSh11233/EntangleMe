from typing import Optional

import pydantic

from classiq.interface.chemistry import operator
from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.hamiltonian_evolution.hamiltonian_evolution import (
    HamiltonianEvolution,
)


class ExponentiationOptimization(StrEnum):
    MINIMIZE_DEPTH = "MINIMIZE_DEPTH"
    MINIMIZE_ERROR = "MINIMIZE_ERROR"


class ExponentiationConstraints(pydantic.BaseModel):
    max_depth: Optional[pydantic.PositiveInt] = pydantic.Field(
        default=None, description="Maximum depth of the exponentiation circuit."
    )
    max_error: Optional[pydantic.PositiveFloat] = pydantic.Field(
        default=None,
        description="Maximum approximation error of the exponentiation circuit.",
    )
    model_config = pydantic.ConfigDict(frozen=True)


class Exponentiation(HamiltonianEvolution):
    """
    Exponentiation of a Hermitian Pauli sum operator.
    """

    evolution_coefficient: float = pydantic.Field(
        default=1.0, description="A global coefficient multiplying the operator."
    )
    constraints: ExponentiationConstraints = pydantic.Field(
        default_factory=ExponentiationConstraints,
        description="Constraints for the exponentiation.",
    )
    optimization: ExponentiationOptimization = pydantic.Field(
        default=ExponentiationOptimization.MINIMIZE_DEPTH,
        description="What attribute to optimize.",
    )

    @pydantic.field_validator("pauli_operator")
    @classmethod
    def _validate_is_hermitian(cls, pauli_operator: PauliOperator) -> PauliOperator:
        return operator.validate_operator_is_hermitian(pauli_operator)
