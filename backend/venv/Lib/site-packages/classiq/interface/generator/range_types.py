import math
from typing import Generic, Optional, TypeVar

import pydantic
from pydantic import BaseModel, ConfigDict
from typing_extensions import Self

from classiq.interface.exceptions import ClassiqValueError

RangeType = TypeVar("RangeType", int, float)

# math.isclose is symmetric and well equipped to avoid unwanted scenarios while numpy's isn't
# see https://github.com/numpy/numpy/issues/10161
# however math's default values are not good for comparing against zeros
DEF_ATOL: float = 1e-08
DEF_RTOL: float = 1e-05


class Range(BaseModel, Generic[RangeType]):
    lower_bound: Optional[RangeType] = None
    upper_bound: Optional[RangeType] = None
    model_config = ConfigDict(frozen=True)

    @pydantic.model_validator(mode="after")
    def _validate_bounds_order(self) -> Self:
        lower_bound = self.lower_bound
        upper_bound = self.upper_bound

        if (
            lower_bound is not None
            and upper_bound is not None
            and lower_bound > upper_bound
        ):
            raise ClassiqValueError("lower bound must not be greater than upper bound")

        return self

    def is_lower_bound_sat_by(
        self, value: float, atol: float = DEF_ATOL, rtol: float = DEF_RTOL
    ) -> bool:
        return (
            value >= self.lower_bound
            or math.isclose(value, self.lower_bound, abs_tol=atol, rel_tol=rtol)
            if self.lower_bound is not None
            else True
        )

    def is_upper_bound_sat_by(
        self, value: float, atol: float = DEF_ATOL, rtol: float = DEF_RTOL
    ) -> bool:
        return (
            value <= self.upper_bound
            or math.isclose(value, self.upper_bound, abs_tol=atol, rel_tol=rtol)
            if self.upper_bound is not None
            else True
        )

    def is_range_sat_by(self, value: float) -> bool:
        return self.is_upper_bound_sat_by(value) and self.is_lower_bound_sat_by(value)


NonNegativeIntRange = Range[pydantic.NonNegativeInt]
NonNegativeFloatRange = Range[pydantic.NonNegativeFloat]
