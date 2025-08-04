from pydantic import BaseModel

from classiq.interface.enum_utils import StrEnum
from classiq.interface.helpers.custom_pydantic_types import (
    PydanticNonOneProbabilityFloat,
)


# it seems to be ambiguous in this class. it is Identical to the Metrics, up to  the
# attribute RANDOM, However RANDOM isn't really used or treated in any part of the code.
# The excision of the two classes is maybe in order to separate between Metrics that are
# used and not used for Optimization, however LOSS_OF_FIDELITY and MAX_PROBABILITY
# are in StatePrepOptimizationMethod, and it seems that they aren't use
# for optimization.
class StatePrepOptimizationMethod(StrEnum):
    KL = "KL"
    L2 = "L2"
    L1 = "L1"
    LOSS_OF_FIDELITY = "LOSS_OF_FIDELITY"
    MAX_PROBABILITY = "MAX_PROBABILITY"
    RANDOM = "RANDOM"


class OptimizationType(StrEnum):
    DEPTH = "depth"
    TWO_QUBIT_GATES = "two_qubit_gates"


class Optimization(BaseModel):
    approximation_error: PydanticNonOneProbabilityFloat = 0.0
    optimization_type: OptimizationType = OptimizationType.DEPTH
