from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.preferences.optimization import (
    StatePrepOptimizationMethod,
)

_AMPLITUDE_SUPPORTING_METRICS: frozenset = frozenset(
    {"L2", "L1", "MAX_PROBABILITY", "TOTAL_VARIATION"}
)

_ZERO_DIVERGENT_METRICS: frozenset = frozenset({"KL", "BHATTACHARYYA"})


class Metrics(StrEnum):
    KL = "KL"
    L2 = "L2"
    L1 = "L1"
    MAX_PROBABILITY = "MAX_PROBABILITY"
    LOSS_OF_FIDELITY = "LOSS_OF_FIDELITY"
    TOTAL_VARIATION = "TOTAL_VARIATION"
    HELLINGER = "HELLINGER"
    BHATTACHARYYA = "BHATTACHARYYA"

    @classmethod
    def from_sp_optimization_method(
        cls, sp_opt_method: StatePrepOptimizationMethod
    ) -> "Metrics":
        try:
            return Metrics(sp_opt_method.value)
        except ValueError:
            raise ClassiqValueError(
                f"Failed to convert {sp_opt_method} to an error metric"
            ) from None

    @property
    def supports_amplitudes(self) -> bool:
        return self.value in _AMPLITUDE_SUPPORTING_METRICS

    @property
    def possibly_diverges(self) -> bool:
        return self.value in _ZERO_DIVERGENT_METRICS
