from collections.abc import Iterable
from typing import Final, Optional

import pydantic
from pydantic import ConfigDict

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.arith.arithmetic_operations import (
    MODULO_WITH_FRACTION_PLACES_ERROR_MSG,
    ArithmeticOperationParams,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import get_zero_input_name

from classiq.model_expansions.arithmetic import NumericAttributes
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_bitwise_invert,
    compute_result_attrs_negate,
)

UNARY_ARG_NAME: Final[str] = "arg"


class UnaryOpParams(ArithmeticOperationParams):
    arg: RegisterArithmeticInfo
    inplace: bool = False

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        return int(self.is_inplaced()) * (
            max(self.arg.integer_part_size - self.result_register.integer_part_size, 0)
            + max(self.arg.fraction_places - self.result_register.fraction_places, 0)
        )

    def should_add_zero_inputs(self) -> bool:
        return not self.is_inplaced() or self.zero_input_for_extension() > 0

    def zero_input_for_extension(self) -> pydantic.NonNegativeInt:
        return max(0, self.result_register.size - self.arg.size)

    def _create_ios(self) -> None:
        self._inputs = {UNARY_ARG_NAME: self.arg}
        self._outputs = {self.output_name: self.result_register}

        zero_input_name = get_zero_input_name(self.output_name)
        if not self.is_inplaced():
            self._outputs[UNARY_ARG_NAME] = self.arg
            zero_input_register = self.result_register
            self._zero_inputs = {zero_input_name: zero_input_register}
            return
        if self.zero_input_for_extension() > 0:
            output_extension_size = self.zero_input_for_extension()
            self._create_zero_input_registers({zero_input_name: output_extension_size})
        if self.garbage_output_size() > 0:
            self._outputs[self.garbage_output_name] = RegisterArithmeticInfo(
                size=self.garbage_output_size()
            )

    def is_inplaced(self) -> bool:
        return self.inplace

    def get_params_inplace_options(self) -> Iterable["UnaryOpParams"]:
        params_kwargs = self.model_copy().model_dump()
        params_kwargs["inplace"] = True
        yield self.__class__(**params_kwargs)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BitwiseInvert(UnaryOpParams):
    output_name = "inverted"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        arg_attrs = NumericAttributes.from_register_arithmetic_info(
            self.arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_bitwise_invert(
            arg_attrs, self.machine_precision
        )

        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            fraction_places=result_attrs.fraction_digits,
            is_signed=result_attrs.is_signed and self._include_sign,
        )


class Negation(UnaryOpParams):
    bypass_bounds_validation: bool = pydantic.Field(
        default=False
    )  # True for efficient subtraction
    output_name = "negated"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        arg_attrs = NumericAttributes.from_register_arithmetic_info(
            self.arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_negate(arg_attrs, self.machine_precision)
        is_signed = result_attrs.is_signed and self._include_sign
        bounds = result_attrs.bounds
        if self.output_size and not self.bypass_bounds_validation:
            if result_attrs.fraction_digits:
                raise ValueError(MODULO_WITH_FRACTION_PLACES_ERROR_MSG)
            max_bounds = RegisterArithmeticInfo.get_maximal_bounds(
                size=self.output_size, is_signed=False, fraction_places=0
            )
            bounds = number_utils.bounds_cut(bounds, max_bounds)
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            fraction_places=result_attrs.fraction_digits,
            is_signed=is_signed,
            bypass_bounds_validation=self.bypass_bounds_validation,
            bounds=bounds,
        )

    def zero_input_for_extension(self) -> pydantic.NonNegativeInt:
        arg_integers = self.arg.size - self.arg.fraction_places
        result_integers = (
            self.result_register.size - self.result_register.fraction_places
        )
        return result_integers - arg_integers


class Sign(UnaryOpParams):
    output_name = "sign"

    @pydantic.field_validator("output_size")
    @classmethod
    def _validate_output_size(
        cls, output_size: Optional[pydantic.PositiveInt]
    ) -> pydantic.PositiveInt:
        if output_size is not None and output_size != 1:
            raise ClassiqValueError("Sign output size must be 1")
        return 1

    def _get_result_register(self) -> RegisterArithmeticInfo:
        return RegisterArithmeticInfo(size=1, fraction_places=0, is_signed=False)

    def is_inplaced(self) -> bool:
        return self.inplace and self.arg.is_signed
