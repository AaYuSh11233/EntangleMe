import pydantic

from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.ansatz_library import (
    EntanglingLayersArgs,
    HypercubeArgs,
    RandomArgs,
    RandomTwoQubitGatesArgs,
    SeparateU3Args,
    TwoLocalArgs,
)


class CustomAnsatzType(StrEnum):
    TwoLocal = "TwoLocal"
    SeparateU3 = "SeparateU3"
    Hypercube = "Hypercube"
    EntanglingLayers = "EntanglingLayers"
    Random = "Random"
    RandomTwoQubitGates = "RandomTwoQubitGates"


CUSTOM_ANSATZ_ARGS_MAPPING: dict[CustomAnsatzType, type[pydantic.BaseModel]] = {
    CustomAnsatzType.TwoLocal: TwoLocalArgs,
    CustomAnsatzType.SeparateU3: SeparateU3Args,
    CustomAnsatzType.Hypercube: HypercubeArgs,
    CustomAnsatzType.EntanglingLayers: EntanglingLayersArgs,
    CustomAnsatzType.Random: RandomArgs,
    CustomAnsatzType.RandomTwoQubitGates: RandomTwoQubitGatesArgs,
}
