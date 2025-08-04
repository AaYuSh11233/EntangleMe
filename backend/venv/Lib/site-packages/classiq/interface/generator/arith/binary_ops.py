import math
from collections.abc import Iterable
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
)

import pydantic
from pydantic import BaseModel
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Self

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith import argument_utils, number_utils
from classiq.interface.generator.arith.argument_utils import (
    RegisterOrConst,
)
from classiq.interface.generator.arith.arithmetic_operations import (
    MODULO_WITH_FRACTION_PLACES_ERROR_MSG,
    ArithmeticOperationParams,
)
from classiq.interface.generator.arith.ast_node_rewrite import (
    NOT_POWER_OF_TWO_ERROR_MSG,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.arith.unary_ops import Negation
from classiq.interface.generator.function_params import get_zero_input_name

from classiq.model_expansions.arithmetic import NumericAttributes
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_add,
    compute_result_attrs_assign,
    compute_result_attrs_bitwise_and,
    compute_result_attrs_bitwise_or,
    compute_result_attrs_bitwise_xor,
    compute_result_attrs_lshift,
    compute_result_attrs_modulo,
    compute_result_attrs_multiply,
    compute_result_attrs_power,
    compute_result_attrs_rshift,
    compute_result_attrs_subtract,
)

LeftDataT = TypeVar("LeftDataT")
RightDataT = TypeVar("RightDataT")
_NumericArgumentInplaceErrorMessage: str = "Cannot inplace the numeric argument {}"
_FLOATING_POINT_MODULO_ERROR_MESSAGE: str = "Floating point modulo not supported"
BOOLEAN_OP_WITH_FRACTIONS_ERROR: str = (
    "Boolean operations are only defined for integers"
)
DEFAULT_LEFT_ARG_NAME: str = "left_arg"
DEFAULT_RIGHT_ARG_NAME: str = "right_arg"
Numeric = (float, int)

RegisterOrInt = Union[int, RegisterArithmeticInfo]


class ArgToInplace(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class BinaryOpParams(
    ArithmeticOperationParams, BaseModel, Generic[LeftDataT, RightDataT]
):
    left_arg: LeftDataT
    right_arg: RightDataT
    left_arg_name: ClassVar[str] = DEFAULT_LEFT_ARG_NAME
    right_arg_name: ClassVar[str] = DEFAULT_RIGHT_ARG_NAME

    @pydantic.model_validator(mode="before")
    @classmethod
    def _clone_repeated_arg(cls, values: Any) -> dict[str, Any]:
        if isinstance(values, dict):
            left_arg = values.get("left_arg")
            right_arg = values.get("right_arg")

            if left_arg is right_arg and isinstance(left_arg, pydantic.BaseModel):
                # In case both arguments refer to the same object, copy it.
                # This prevents changes performed on one argument to affect the other.
                values["right_arg"] = left_arg.model_copy(deep=True)
        return values

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        return 0

    def _create_ios(self) -> None:
        self._inputs = dict()
        if isinstance(self.left_arg, RegisterArithmeticInfo):
            self._inputs[self.left_arg_name] = self.left_arg
        if isinstance(self.right_arg, RegisterArithmeticInfo):
            self._inputs[self.right_arg_name] = self.right_arg
        self._outputs = {**self._inputs, self.output_name: self.result_register}

        garbage_size = self.garbage_output_size()
        if garbage_size > 0:
            self._outputs[self.garbage_output_name] = RegisterArithmeticInfo(
                size=garbage_size
            )

        zero_input_name = get_zero_input_name(self.output_name)
        zero_input_size = self.result_register.size + garbage_size
        self._zero_inputs = {
            zero_input_name: RegisterArithmeticInfo(size=zero_input_size)
        }

    def is_inplaced(self) -> bool:
        return False

    def get_params_inplace_options(self) -> Iterable["BinaryOpParams"]:
        return ()


class InplacableBinaryOpParams(
    BinaryOpParams[LeftDataT, RightDataT], Generic[LeftDataT, RightDataT]
):
    inplace_arg: Optional[ArgToInplace] = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate_inplace_arg(cls, values: Any) -> dict[str, Any]:
        if isinstance(values, dict):
            left_arg = values.get("left_arg")
            right_arg = values.get("right_arg")
            inplace_arg: Optional[ArgToInplace] = values.get("inplace_arg")
            if inplace_arg == ArgToInplace.RIGHT and isinstance(right_arg, Numeric):
                raise ClassiqValueError(
                    _NumericArgumentInplaceErrorMessage.format(right_arg)
                )
            elif inplace_arg == ArgToInplace.LEFT and isinstance(left_arg, Numeric):
                raise ClassiqValueError(
                    _NumericArgumentInplaceErrorMessage.format(left_arg)
                )
        return values

    def _create_ios(self) -> None:
        BinaryOpParams._create_ios(self)
        if self.inplace_arg is None:
            return
        inplace_arg_name = (
            self.left_arg_name
            if self.inplace_arg == ArgToInplace.LEFT
            else self.right_arg_name
        )
        self._outputs.pop(inplace_arg_name)

        self._set_inplace_zero_inputs(inplace_arg_name, self.garbage_output_size())

    def _set_inplace_zero_inputs(
        self, inplace_arg_name: str, garbage_size: int
    ) -> None:
        zero_input_name = get_zero_input_name(self.output_name)
        self._zero_inputs.pop(zero_input_name)

        num_extra_qubits = self.outputs[self.output_name].size - (
            self._inputs[inplace_arg_name].size - garbage_size
        )
        if num_extra_qubits > 0:
            self._zero_inputs[zero_input_name] = RegisterArithmeticInfo(
                size=num_extra_qubits
            )

    def is_inplaced(self) -> bool:
        return self.inplace_arg is not None

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        if self.inplace_arg is None:
            return 0
        arg = self.left_arg if self.inplace_arg == ArgToInplace.LEFT else self.right_arg
        return max(
            0, arg.integer_part_size - self.result_register.integer_part_size  # type: ignore[attr-defined]
        ) + max(
            0, arg.fraction_places - self.result_register.fraction_places  # type: ignore[attr-defined]
        )

    def _carried_arguments(self) -> tuple[Optional[LeftDataT], Optional[RightDataT]]:
        if self.inplace_arg == ArgToInplace.RIGHT and isinstance(
            self.left_arg, RegisterArithmeticInfo
        ):
            return self.left_arg, None  # type: ignore[return-value]
        elif self.inplace_arg == ArgToInplace.LEFT and isinstance(
            self.right_arg, RegisterArithmeticInfo
        ):
            return None, self.right_arg  # type: ignore[return-value]
        elif self.inplace_arg is not None:
            return None, None
        return self.left_arg, self.right_arg

    def _get_binary_op_inplace_options(self) -> Iterable[ArgToInplace]:
        right_arg = getattr(self, "right_arg", None)
        left_arg = getattr(self, "left_arg", None)
        if isinstance(right_arg, RegisterArithmeticInfo) and isinstance(
            left_arg, RegisterArithmeticInfo
        ):
            if left_arg.size > right_arg.size:
                yield ArgToInplace.LEFT
                yield ArgToInplace.RIGHT
            else:
                yield ArgToInplace.RIGHT
                yield ArgToInplace.LEFT
        elif isinstance(right_arg, RegisterArithmeticInfo):
            yield ArgToInplace.RIGHT
        elif isinstance(left_arg, RegisterArithmeticInfo):
            yield ArgToInplace.LEFT

    def get_params_inplace_options(self) -> Iterable["InplacableBinaryOpParams"]:
        params_kwargs = self.model_copy().__dict__
        for inplace_arg in self._get_binary_op_inplace_options():
            params_kwargs["inplace_arg"] = inplace_arg
            yield self.__class__(**params_kwargs)


class BinaryOpWithIntInputs(BinaryOpParams[RegisterOrInt, RegisterOrInt]):
    @pydantic.model_validator(mode="after")
    def validate_int_registers(self) -> Self:
        left_arg = self.left_arg
        is_left_arg_float_register = (
            isinstance(left_arg, RegisterArithmeticInfo)
            and left_arg.fraction_places > 0
        )
        right_arg = self.right_arg
        is_right_arg_float_register = (
            isinstance(right_arg, RegisterArithmeticInfo)
            and right_arg.fraction_places > 0
        )
        if is_left_arg_float_register or is_right_arg_float_register:
            raise ClassiqValueError(BOOLEAN_OP_WITH_FRACTIONS_ERROR)
        return self


class BinaryOpWithFloatInputs(BinaryOpParams[RegisterOrConst, RegisterOrConst]):
    pass


class BitwiseAnd(BinaryOpWithIntInputs):
    output_name = "bitwise_and"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_bitwise_and(
            left_attrs, right_attrs, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            is_signed=self._include_sign and result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
        )


class BitwiseOr(BinaryOpWithIntInputs):
    output_name = "bitwise_or"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_bitwise_or(
            left_attrs, right_attrs, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            is_signed=self._include_sign and result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
        )


# TODO: fix diamond inheritance
class BitwiseXor(
    BinaryOpWithIntInputs, InplacableBinaryOpParams[RegisterOrInt, RegisterOrInt]
):
    output_name = "bitwise_xor"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_bitwise_xor(
            left_attrs, right_attrs, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            is_signed=self._include_sign and result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
        )


class Adder(InplacableBinaryOpParams[RegisterOrConst, RegisterOrConst]):
    output_name = "sum"

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )

        if self._is_zero(self.left_arg) or self._is_zero(self.right_arg):
            other_arg_attrs = (
                right_attrs if self._is_zero(self.left_arg) else left_attrs
            )
            result_attrs = compute_result_attrs_assign(
                other_arg_attrs, self.machine_precision
            )
        else:
            result_attrs = compute_result_attrs_add(
                left_attrs, right_attrs, self.machine_precision
            )

        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            fraction_places=result_attrs.fraction_digits,
            is_signed=self._include_sign and result_attrs.is_signed,
            bounds=result_attrs.bounds if self._include_sign else None,
        )

    @staticmethod
    def _is_zero(arg: RegisterOrConst) -> bool:
        return isinstance(arg, float) and arg == 0


class Subtractor(InplacableBinaryOpParams[RegisterOrConst, RegisterOrConst]):
    output_name = "difference"

    @staticmethod
    def _get_effective_arg(
        arg: RegisterOrConst, machine_precision: int
    ) -> RegisterOrConst:
        return argument_utils.limit_fraction_places(arg, machine_precision)

    @property
    def effective_left_arg(self) -> RegisterOrConst:
        return self._get_effective_arg(self.left_arg, self.machine_precision)

    @property
    def effective_right_arg(self) -> RegisterOrConst:
        return self._get_effective_arg(self.right_arg, self.machine_precision)

    @staticmethod
    def _is_arg_trimmed_register(arg: RegisterOrConst, machine_precision: int) -> bool:
        return (
            isinstance(arg, RegisterArithmeticInfo)
            and arg.fraction_places > machine_precision
        )

    @property
    def left_arg_is_trimmed_register(self) -> bool:
        return self._is_arg_trimmed_register(self.left_arg, self.machine_precision)

    @property
    def right_arg_is_trimmed_register(self) -> bool:
        return self._is_arg_trimmed_register(self.right_arg, self.machine_precision)

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_subtract(
            left_attrs, right_attrs, self.machine_precision
        )

        size = self.output_size or result_attrs.size
        is_signed = self._include_sign and result_attrs.is_signed
        return RegisterArithmeticInfo(
            size=size,
            fraction_places=result_attrs.fraction_digits,
            is_signed=is_signed,
            bounds=self._legal_bounds(
                result_attrs.bounds,
                RegisterArithmeticInfo.get_maximal_bounds(
                    size=size,
                    is_signed=is_signed,
                    fraction_places=result_attrs.fraction_digits,
                ),
            ),
        )

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        if (
            not self.left_arg_is_trimmed_register
            and not self.right_arg_is_trimmed_register
        ):
            return self._untrimmed_garbage_output_size()
        if not self.is_inplaced():
            return 0
        inplace_arg_name = (
            self.left_arg_name
            if self.inplace_arg == ArgToInplace.LEFT
            else self.right_arg_name
        )
        return max(
            0,
            self._inputs[inplace_arg_name].fraction_places
            - self.result_register.fraction_places,
        )

    def _untrimmed_garbage_output_size(self) -> pydantic.NonNegativeInt:
        if not isinstance(self.effective_right_arg, RegisterArithmeticInfo):
            adder_params = Adder(
                left_arg=self.effective_left_arg,
                right_arg=-self.effective_right_arg,
                output_size=self.output_size,
                inplace_arg=self.inplace_arg,
                machine_precision=self.machine_precision,
            )
            return adder_params.garbage_output_size()

        negation_params = Negation(
            arg=self.effective_right_arg,
            output_size=self.negation_output_size,
            inplace=self.should_inplace_negation,
            bypass_bounds_validation=True,
            machine_precision=self.machine_precision,
        )
        negation_result = negation_params.result_register
        if self.output_size is None and max(self.effective_right_arg.bounds) > 0:
            bounds = (
                -max(self.effective_right_arg.bounds),
                -min(self.effective_right_arg.bounds),
            )
            negation_result = RegisterArithmeticInfo(
                size=negation_result.size,
                fraction_places=negation_result.fraction_places,
                is_signed=True,
                bounds=bounds,
                bypass_bounds_validation=True,
            )
        adder_params = Adder(
            left_arg=self.effective_left_arg,
            right_arg=negation_result,
            output_size=self.output_size,
            inplace_arg=self.arg_to_inplace_adder,
            machine_precision=self.machine_precision,
        )
        negation_garbage_size = negation_params.garbage_output_size() * int(
            not self.should_uncompute_negation
        )
        return adder_params.garbage_output_size() + negation_garbage_size

    @property
    def should_uncompute_negation(self) -> bool:
        return self.inplace_arg == ArgToInplace.LEFT

    def _expected_negation_output_size(self) -> int:
        return argument_utils.fraction_places(self.effective_right_arg) + min(
            self.result_register.integer_part_size,
            number_utils.bounds_to_integer_part_size(
                *(-bound for bound in argument_utils.bounds(self.effective_right_arg))
            ),
        )

    @property
    def negation_output_size(self) -> int:
        if self.output_size:
            return min(self.output_size, self._expected_negation_output_size())
        return self._expected_negation_output_size()

    @property
    def should_inplace_negation(self) -> bool:
        return self.inplace_arg is not None

    @property
    def arg_to_inplace_adder(self) -> ArgToInplace:
        return (
            ArgToInplace.LEFT
            if self.inplace_arg == ArgToInplace.LEFT
            else ArgToInplace.RIGHT
        )


class Multiplier(BinaryOpWithFloatInputs):
    output_name = "product"

    def expected_fraction_places(self) -> int:
        return argument_utils.fraction_places(
            argument_utils.limit_fraction_places(self.left_arg, self.machine_precision)
        ) + argument_utils.fraction_places(
            argument_utils.limit_fraction_places(self.right_arg, self.machine_precision)
        )

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_type_or_constant(
            self.left_arg, self.machine_precision
        )
        right_attrs = NumericAttributes.from_type_or_constant(
            self.right_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_multiply(
            left_attrs, right_attrs, self.machine_precision
        )
        fraction_places = result_attrs.fraction_digits
        bounds = result_attrs.bounds
        if self.output_size:
            if fraction_places:
                raise ValueError(MODULO_WITH_FRACTION_PLACES_ERROR_MSG)
            max_bounds = RegisterArithmeticInfo.get_maximal_bounds(
                size=self.output_size, is_signed=False, fraction_places=0
            )
            bounds = number_utils.bounds_cut(bounds, max_bounds)

        size = self.output_size or result_attrs.size
        is_signed = self._include_sign and result_attrs.is_signed
        return RegisterArithmeticInfo(
            size=size,
            fraction_places=fraction_places,
            is_signed=is_signed,
            bounds=self._legal_bounds(
                bounds,
                RegisterArithmeticInfo.get_maximal_bounds(
                    size=size, is_signed=is_signed, fraction_places=fraction_places
                ),
            ),
        )

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        return max(
            0, self.expected_fraction_places() - self.result_register.fraction_places
        )


class Comparator(BinaryOpWithFloatInputs):
    output_size: Literal[1] = 1

    def _get_result_register(self) -> RegisterArithmeticInfo:
        return RegisterArithmeticInfo(size=1)


class Equal(Comparator):
    output_name = "is_equal"


class NotEqual(Comparator):
    output_name = "is_not_equal"


class GreaterThan(Comparator):
    output_name = "is_greater_than"


class GreaterEqual(Comparator):
    output_name = "is_greater_equal"


class LessThan(Comparator):
    output_name = "is_less_than"


class LessEqual(Comparator):
    output_name = "is_less_equal"


class Power(BinaryOpParams[RegisterArithmeticInfo, pydantic.PositiveInt]):
    output_name = "powered"

    @pydantic.field_validator("right_arg", mode="before")
    @classmethod
    def _validate_legal_power(cls, right_arg: Any) -> pydantic.PositiveInt:
        if not float(right_arg).is_integer():
            raise ClassiqValueError("Power must be an integer")
        if right_arg <= 0:
            raise ClassiqValueError("Power must be greater than one")
        return int(right_arg)

    def expected_fraction_places(self) -> int:
        return (
            argument_utils.fraction_places(
                argument_utils.limit_fraction_places(
                    self.left_arg, self.machine_precision
                )
            )
            * self.right_arg
        )

    def _get_result_register(self) -> RegisterArithmeticInfo:
        if self.output_size:
            return RegisterArithmeticInfo(size=self.output_size)

        left_attrs = NumericAttributes.from_register_arithmetic_info(
            self.left_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_power(
            left_attrs, self.right_arg, self.machine_precision
        )

        return RegisterArithmeticInfo(
            size=result_attrs.size,
            is_signed=result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
            bounds=result_attrs.bounds,
        )

    def _get_inner_action_garbage_size(
        self,
        action_type: Union[type["Power"], type[Multiplier]],
        *,
        arg: RegisterArithmeticInfo,
        action_right_arg: RegisterOrConst,
        compute_power: int,
    ) -> pydantic.NonNegativeInt:
        inner_compute_power_params = Power(
            left_arg=arg,
            right_arg=compute_power,
            output_size=self.output_size,
            machine_precision=self.machine_precision,
        )
        return action_type(
            left_arg=inner_compute_power_params.result_register,
            right_arg=action_right_arg,
            output_size=self.output_size,
            machine_precision=self.machine_precision,
        ).garbage_output_size()

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        arg = self.left_arg
        power = self.right_arg
        if power == 1:
            return 0
        if (
            power == 2
            or (arg.size == 1 and arg.fraction_places == 0)
            or self.output_size == 1
        ):
            return max(
                0,
                self.expected_fraction_places() - self.result_register.fraction_places,
            )

        if power % 2 == 0:
            return self._get_inner_action_garbage_size(
                Power, arg=arg, action_right_arg=power // 2, compute_power=2
            )
        return self._get_inner_action_garbage_size(
            Multiplier, arg=arg, action_right_arg=arg, compute_power=power - 1
        )


class EffectiveUnaryOpParams(
    InplacableBinaryOpParams[RegisterArithmeticInfo, RightDataT], Generic[RightDataT]
):
    left_arg_name = "arg"


class LShift(EffectiveUnaryOpParams[pydantic.NonNegativeInt]):
    output_name = "left_shifted"
    inplace_arg: Optional[ArgToInplace] = ArgToInplace.LEFT

    @pydantic.model_validator(mode="after")
    def _validate_legal_modulo(self) -> Self:
        output_size = self.output_size
        if output_size is None:
            return self
        arg = self.left_arg
        shift = self.right_arg
        if not isinstance(arg, RegisterArithmeticInfo):
            raise ClassiqValueError("left arg must be a RegisterArithmeticInfo")
        if not isinstance(shift, int):
            raise ClassiqValueError("Shift must be an integer")
        assert arg.fraction_places - shift <= 0, _FLOATING_POINT_MODULO_ERROR_MESSAGE
        return self

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        if self.inplace_arg is None or self.output_size is None:
            return 0
        extra_result_lsbs = min(
            self.output_size, max(self.right_arg - self.left_arg.fraction_places, 0)
        )
        return max(self.left_arg.size + extra_result_lsbs - self.output_size, 0)

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_register_arithmetic_info(
            self.left_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_lshift(
            left_attrs, self.right_arg, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            is_signed=self._include_sign and result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
            bounds=result_attrs.bounds if not self.output_size else None,
        )


class RShift(EffectiveUnaryOpParams[pydantic.NonNegativeInt]):
    output_name = "right_shifted"
    inplace_arg: Optional[ArgToInplace] = ArgToInplace.LEFT

    @staticmethod
    def _shifted_fraction_places(*, arg: RegisterArithmeticInfo, shift: int) -> int:
        return arg.fraction_places * int(arg.is_signed or shift < arg.size)

    @pydantic.model_validator(mode="after")
    def _validate_legal_modulo(self) -> Self:
        output_size = self.output_size
        if output_size is None:
            return self
        arg = self.left_arg
        shift = self.right_arg
        if not isinstance(arg, RegisterArithmeticInfo):
            raise ClassiqValueError("left arg must be a RegisterArithmeticInfo")
        if not isinstance(shift, int):
            raise ClassiqValueError("Shift must be an integer")
        assert (
            self._shifted_fraction_places(arg=arg, shift=shift) == 0
        ), _FLOATING_POINT_MODULO_ERROR_MESSAGE
        return self

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        if self.inplace_arg is None:
            return 0
        if self.output_size is None:
            return min(self.left_arg.size, self.right_arg)
        if self.right_arg >= self.left_arg.size:
            return self.left_arg.size
        return self.right_arg + max(
            self.left_arg.size - self.right_arg - self.output_size, 0
        )

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_register_arithmetic_info(
            self.left_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_rshift(
            left_attrs, self.right_arg, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=self.output_size or result_attrs.size,
            is_signed=self._include_sign and result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
            bounds=result_attrs.bounds if not self.output_size else None,
        )


class CyclicShift(EffectiveUnaryOpParams[int]):
    output_name = "cyclic_shifted"
    inplace_arg: Optional[ArgToInplace] = ArgToInplace.LEFT

    @pydantic.model_validator(mode="after")
    def _validate_legal_modulo(self) -> Self:
        output_size = self.output_size
        if output_size is None:
            return self
        arg = self.left_arg
        if not isinstance(arg, RegisterArithmeticInfo):
            raise ClassiqValueError("left arg must be a RegisterArithmeticInfo")
        assert arg.fraction_places == 0, _FLOATING_POINT_MODULO_ERROR_MESSAGE
        return self

    def garbage_output_size(self) -> pydantic.NonNegativeInt:
        if self.inplace_arg is None:
            return 0
        return max(0, self.left_arg.size - self.result_register.size)

    def _get_result_register(self) -> RegisterArithmeticInfo:
        return RegisterArithmeticInfo(
            size=self.output_size or self.left_arg.size,
            is_signed=self._include_sign and self.left_arg.is_signed,
            fraction_places=self.left_arg.fraction_places,
        )


class Modulo(EffectiveUnaryOpParams[int]):
    output_name = "modulus"
    inplace_arg: Optional[ArgToInplace] = ArgToInplace.LEFT

    @pydantic.field_validator("left_arg", mode="before")
    @classmethod
    def _validate_left_arg_is_integer(
        cls, left_arg: RegisterArithmeticInfo
    ) -> RegisterArithmeticInfo:
        assert left_arg.fraction_places == 0, _FLOATING_POINT_MODULO_ERROR_MESSAGE
        return left_arg

    @pydantic.field_validator("right_arg", mode="before")
    @classmethod
    def _validate_right_arg_is_a_power_of_two(
        cls, right_arg: int, info: ValidationInfo
    ) -> int:
        repr_qubits_float = math.log2(right_arg)
        repr_qubits = round(repr_qubits_float)
        assert abs(repr_qubits - repr_qubits_float) < 10**-8, NOT_POWER_OF_TWO_ERROR_MSG
        output_size = info.data.get("output_size")
        if output_size is not None:
            repr_qubits = min(repr_qubits, output_size)
        info.data["output_size"] = None
        return 2 ** (repr_qubits)

    def _get_result_register(self) -> RegisterArithmeticInfo:
        left_attrs = NumericAttributes.from_register_arithmetic_info(
            self.left_arg, self.machine_precision
        )
        result_attrs = compute_result_attrs_modulo(
            left_attrs, self.right_arg, self.machine_precision
        )
        return RegisterArithmeticInfo(
            size=result_attrs.size,
            is_signed=result_attrs.is_signed,
            fraction_places=result_attrs.fraction_digits,
            bounds=result_attrs.bounds,
        )
