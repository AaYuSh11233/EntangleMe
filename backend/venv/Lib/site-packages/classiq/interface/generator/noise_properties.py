from typing import Optional

import pydantic
from pydantic import BaseModel

from classiq.interface.helpers.custom_pydantic_types import PydanticProbabilityFloat


class NoiseProperties(BaseModel):
    measurement_bit_flip_probability: Optional[PydanticProbabilityFloat] = (
        pydantic.Field(
            default=None,
            description="Probability of measuring the wrong value for each qubit.",
        )
    )
