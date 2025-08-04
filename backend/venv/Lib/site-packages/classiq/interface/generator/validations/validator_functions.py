from collections.abc import Iterable, Sequence, Sized
from typing import TypeVar

import numpy as np

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.custom_pydantic_types import PydanticProbabilityFloat

NOT_SUM_TO_ONE_ERROR = "Probabilities do not sum to 1"

SUM_TO_ONE_SENSITIVITY = 8

Amplitude = TypeVar("Amplitude", tuple[float, ...], list[complex])


def _is_power_of_two(vector: Sized) -> bool:
    n = len(vector)
    return (n != 0) and (n & (n - 1) == 0)


def is_amplitudes_sum_to_one(amp: Iterable[complex]) -> bool:
    return round(sum(abs(np.array(amp)) ** 2), SUM_TO_ONE_SENSITIVITY) == 1


def is_probabilities_sum_to_one(pro: Iterable[PydanticProbabilityFloat]) -> bool:
    return round(sum(pro), SUM_TO_ONE_SENSITIVITY) == 1


def validate_amplitudes(amp: Amplitude) -> Amplitude:
    if not is_amplitudes_sum_to_one(amp):
        raise ClassiqValueError("Amplitudes do not sum to 1")
    if not _is_power_of_two(amp):
        raise ClassiqValueError("Amplitudes length must be power of 2")
    return amp


def validate_probabilities(
    cls: type, pmf: Sequence[PydanticProbabilityFloat]
) -> Sequence[PydanticProbabilityFloat]:
    if not is_probabilities_sum_to_one(pmf):
        raise ClassiqValueError(NOT_SUM_TO_ONE_ERROR)
    if not _is_power_of_two(pmf):
        raise ClassiqValueError("Probabilities length must be power of 2")
    return pmf
