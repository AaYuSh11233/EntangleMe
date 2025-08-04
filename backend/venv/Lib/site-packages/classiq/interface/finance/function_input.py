from typing import Any, Optional, Union

import pydantic
from pydantic import ConfigDict
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.enums.finance_functions import (
    get_finance_function_dict,
)
from classiq.interface.generator.types.builtin_enum_declarations import (
    FinanceFunctionType,
)
from classiq.interface.helpers.custom_pydantic_types import (
    PydanticNonZeroProbabilityFloat,
)


class FunctionCondition(pydantic.BaseModel):
    threshold: float
    larger: bool = pydantic.Field(
        default=False,
        description="When true, function is set when input is larger to threshold and otherwise 0. Default is False.",
    )
    model_config = ConfigDict(frozen=True)


class FinanceFunctionInput(pydantic.BaseModel):
    f: "FinanceFunctionType" = pydantic.Field(
        description="An enumeration of the wanted financial function: VaR, expected "
        "shortfall, European call options or x^2"
    )
    variable: str = pydantic.Field(
        default="x", description="Variable/s of the function"
    )
    condition: FunctionCondition = pydantic.Field(
        description="The condition for the function"
    )
    polynomial_degree: Optional[int] = pydantic.Field(
        default=None,
        description="The polynomial degree of approximation, uses linear approximation by default",
    )
    use_chebyshev_polynomial_approximation: bool = pydantic.Field(
        default=False,
        description="Flag if to use chebyshev polynomial approximation for target function",
    )

    tail_probability: Optional[PydanticNonZeroProbabilityFloat] = pydantic.Field(
        default=None,
        description="The required probability on the tail of the distribution (1 - percentile)",
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _convert_f_if_str(cls, values: Any, info: ValidationInfo) -> dict[str, Any]:
        if isinstance(values, dict):
            f = values.get("f")
        elif isinstance(values, FinanceFunctionInput):
            f = values.f
            values = values.model_dump()
        else:
            f = info.data.get("f")
        if isinstance(f, str) and f in get_finance_function_dict():
            values["f"] = get_finance_function_dict()[f]
        return values

    @pydantic.field_validator("use_chebyshev_polynomial_approximation", mode="before")
    @classmethod
    def _validate_polynomial_flag(
        cls, use_chebyshev_flag: bool, info: ValidationInfo
    ) -> bool:
        if use_chebyshev_flag ^ (info.data.get("polynomial_degree") is None):
            return use_chebyshev_flag
        raise ClassiqValueError(
            "Degree must be positive and use_chebyshev_polynomial_approximation set to True"
        )

    @pydantic.field_validator("f", mode="before")
    @classmethod
    def _validate_finance_function(
        cls, f: Union[int, str, "FinanceFunctionType"]
    ) -> FinanceFunctionType:
        if isinstance(f, FinanceFunctionType):
            return f
        if isinstance(f, int):
            return FinanceFunctionType(f)
        return get_finance_function_dict()[f]

    @pydantic.field_validator("tail_probability", mode="before")
    @classmethod
    def _validate_tail_probability_assignment_for_shortfall(
        cls,
        tail_probability: Optional[PydanticNonZeroProbabilityFloat],
        info: ValidationInfo,
    ) -> Optional[PydanticNonZeroProbabilityFloat]:
        if info.data.get("f") == FinanceFunctionType.SHORTFALL and not tail_probability:
            raise ClassiqValueError(
                "Tail probability must be set for expected shortfall"
            )
        return tail_probability

    model_config = ConfigDict(frozen=True)
