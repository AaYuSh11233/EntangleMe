from collections.abc import Collection, Sequence
from typing import Union

import pydantic
from numpy.typing import ArrayLike
from pydantic import ConfigDict

from classiq.interface.generator.validations.validator_functions import (
    validate_probabilities,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticProbabilityFloat


class PMF(pydantic.BaseModel):
    pmf: tuple[PydanticProbabilityFloat, ...]

    @pydantic.field_validator("pmf")
    @classmethod
    def _validate_pmf(
        cls, pmf: tuple[PydanticProbabilityFloat, ...]
    ) -> Sequence[PydanticProbabilityFloat]:
        return validate_probabilities(cls, pmf)

    model_config = ConfigDict(frozen=True)


class GaussianMoments(pydantic.BaseModel):
    mu: float
    sigma: pydantic.PositiveFloat
    model_config = ConfigDict(frozen=True)


class GaussianMixture(pydantic.BaseModel):
    gaussian_moment_list: tuple[GaussianMoments, ...]
    num_qubits: pydantic.PositiveInt = pydantic.Field(
        description="Number of qubits for the provided state."
    )
    model_config = ConfigDict(frozen=True)


Probabilities = Union[PMF, GaussianMixture]
FlexibleProbabilities = Union[Probabilities, ArrayLike, dict, Collection[float]]
Amplitudes = tuple[float, ...]
FlexibleAmplitudes = Union[ArrayLike, Collection[float]]
Distribution = Union[Amplitudes, Probabilities]


def num_of_qubits(distribution: Distribution) -> int:
    if isinstance(distribution, GaussianMixture):
        return distribution.num_qubits
    if isinstance(distribution, PMF):
        return len(distribution.pmf).bit_length() - 1
    return len(distribution).bit_length() - 1
