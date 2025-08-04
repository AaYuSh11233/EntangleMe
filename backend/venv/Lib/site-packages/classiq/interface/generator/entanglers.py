import pydantic
from pydantic import BaseModel

from classiq.interface.helpers.custom_pydantic_types import PydanticLargerThanOneInteger


class SquareClusterEntanglerParameters(BaseModel):
    num_of_qubits: PydanticLargerThanOneInteger
    schmidt_rank: pydantic.NonNegativeInt


class Open2DClusterEntanglerParameters(BaseModel):
    qubit_count: PydanticLargerThanOneInteger
    schmidt_rank: pydantic.NonNegativeInt
