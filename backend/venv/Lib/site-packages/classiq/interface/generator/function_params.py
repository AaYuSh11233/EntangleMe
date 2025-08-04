import ast
import itertools
import re
from collections.abc import Collection, Iterable, Mapping
from typing import (
    Annotated,
    Any,
    Optional,
    Union,
    get_args,
)

import pydantic
import sympy
from pydantic import BeforeValidator, ConfigDict

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.arithmetic_expression_validator import (
    validate_expression,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.parameters import ParameterFloatType
from classiq.interface.helpers.custom_pydantic_types import PydanticNonEmptyString
from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)

FunctionParamsDiscriminator = str

IOName = PydanticNonEmptyString
ArithmeticIODict = dict[IOName, RegisterArithmeticInfo]

DEFAULT_ZERO_NAME = "zero"
DEFAULT_OUTPUT_NAME = "OUT"
DEFAULT_INPUT_NAME = "IN"

BAD_FUNCTION_ERROR_MSG = "field must be provided to deduce"
NO_DISCRIMINATOR_ERROR_MSG = "Unknown"

REGISTER_SIZES_MISMATCH_ERROR_MSG = "Register sizes differ between inputs and outputs"

BAD_INPUT_REGISTER_ERROR_MSG = "Bad input register name given"
BAD_OUTPUT_REGISTER_ERROR_MSG = "Bad output register name given"
END_BAD_REGISTER_ERROR_MSG = (
    "Register name must be in snake_case and begin with a letter."
)

ALPHANUM_AND_UNDERSCORE = r"[0-9a-zA-Z_]*"
NAME_REGEX = rf"_?[a-zA-Z]{ALPHANUM_AND_UNDERSCORE}"

_UNVALIDATED_FUNCTIONS = ["Arithmetic", "CustomFunction"]

ExecutionExpressionSupportedNodeTypes = Union[
    # binary operation
    ast.BinOp,
    ast.BitOr,
    ast.BitAnd,
    ast.BitXor,
    # binary operation - arithmetic
    ast.Add,
    ast.Mod,
    ast.Sub,
    ast.LShift,
    ast.RShift,
    ast.Mult,
    ast.Div,
    # Unary operations
    ast.UnaryOp,
    ast.USub,
    ast.UAdd,
    ast.Invert,
    # Other
    ast.Expression,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Num,
]

GenerationOnlyExpressionSupportedNodeTypes = Union[
    ast.Pow,
    ast.List,
    ast.Subscript,
    ast.Index,
    ast.Tuple,
    ast.Compare,
    ast.Gt,
    ast.GtE,
    ast.Lt,
    ast.LtE,
    ast.Eq,
    ast.NotEq,
    ast.Call,
    ast.Dict,
    ast.Slice,
    ast.keyword,
    ast.Attribute,
    ast.BoolOp,
    ast.Or,
    ast.And,
    ast.Not,
]

GenerationExpressionSupportedNodeTypes = Union[
    ExecutionExpressionSupportedNodeTypes, GenerationOnlyExpressionSupportedNodeTypes
]


def validate_expression_str(
    expr_str: str, supported_functions: Optional[set[str]] = None
) -> None:
    # By default, no functions are allowed.
    supported_functions = supported_functions or set()

    # We validate the given value is legal and does not contain code that will be executed in our BE.
    validate_expression(
        expr_str,
        supported_nodes=get_args(GenerationExpressionSupportedNodeTypes),
        expression_type="parameter",
        supported_functions=supported_functions,
    )


def validate_parameters(value: Any) -> Any:
    if isinstance(value, str):
        validate_expression_str(value)
    elif isinstance(value, sympy.Expr):
        return str(value)
    try:
        return float(value)
    except ValueError:
        return value


FunctionParamsNumericParameter = Annotated[
    ParameterFloatType, BeforeValidator(validate_parameters)
]


class PortDirection(StrEnum):
    Input = "input"
    Output = "output"
    Inout = "inout"

    def __invert__(self) -> "PortDirection":
        if self is PortDirection.Inout:
            return self
        return (
            PortDirection.Input
            if self is PortDirection.Output
            else PortDirection.Output
        )


def get_zero_input_name(output_name: str) -> str:
    return f"{DEFAULT_ZERO_NAME}_{output_name}"


class FunctionParams(HashablePydanticBaseModel):
    _inputs: ArithmeticIODict = pydantic.PrivateAttr(default_factory=dict)
    _outputs: ArithmeticIODict = pydantic.PrivateAttr(default_factory=dict)
    _zero_inputs: ArithmeticIODict = pydantic.PrivateAttr(default_factory=dict)

    @property
    def inputs(self) -> ArithmeticIODict:
        return self._inputs

    def inputs_full(self, strict_zero_ios: bool = True) -> ArithmeticIODict:
        if strict_zero_ios:
            return self._inputs
        return {**self._inputs, **self._zero_inputs}

    @property
    def outputs(self) -> ArithmeticIODict:
        return self._outputs

    def num_input_qubits(self, strict_zero_ios: bool = True) -> int:
        return sum(reg.size for reg in self.inputs_full(strict_zero_ios).values())

    @property
    def num_output_qubits(self) -> int:
        return sum(reg.size for reg in self.outputs.values())

    @property
    def _input_names(self) -> list[IOName]:
        return list(self._inputs.keys())

    @property
    def _output_names(self) -> list[IOName]:
        return list(self._outputs.keys())

    def _create_zero_input_registers(self, names_and_sizes: Mapping[str, int]) -> None:
        for name, size in names_and_sizes.items():
            self._zero_inputs[name] = RegisterArithmeticInfo(size=size)

    def _create_zero_inputs_from_outputs(self) -> None:
        for name, reg in self._outputs.items():
            zero_input_name = get_zero_input_name(name)
            self._zero_inputs[zero_input_name] = reg

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._create_ios()
        if not self._inputs and not self._zero_inputs:
            self._create_zero_inputs_from_outputs()
        self._validate_io_names()

        if self.discriminator() not in _UNVALIDATED_FUNCTIONS:
            self._validate_total_io_sizes()

    def is_powerable(self, strict_zero_ios: bool = True) -> bool:
        input_names = set(self.inputs_full(strict_zero_ios))
        output_names = set(self._output_names)
        return (
            self.num_input_qubits(strict_zero_ios) == self.num_output_qubits
            and len(input_names) == len(output_names)
            and (len(input_names - output_names) <= 1)
            and (len(output_names - input_names) <= 1)
        )

    def get_power_order(self) -> Optional[int]:
        return None

    def _create_ios(self) -> None:
        pass

    @staticmethod
    def _get_size_of_ios(
        registers: Collection[Optional[RegisterArithmeticInfo]],
    ) -> int:
        return sum(reg.size if reg is not None else 0 for reg in registers)

    def _validate_io_names(self) -> None:
        error_msg: list[str] = []
        error_msg += self._get_error_msg(self._inputs, BAD_INPUT_REGISTER_ERROR_MSG)
        error_msg += self._get_error_msg(self._outputs, BAD_OUTPUT_REGISTER_ERROR_MSG)
        if error_msg:
            error_msg += [END_BAD_REGISTER_ERROR_MSG]
            raise ClassiqValueError("\n".join(error_msg))

    @staticmethod
    def _sum_registers_sizes(registers: Iterable[RegisterArithmeticInfo]) -> int:
        return sum(reg.size for reg in registers)

    def _validate_total_io_sizes(self) -> None:
        total_inputs_size = self._sum_registers_sizes(
            itertools.chain(self._inputs.values(), self._zero_inputs.values())
        )
        total_outputs_size = self._sum_registers_sizes(self._outputs.values())
        if total_inputs_size != total_outputs_size:
            raise ClassiqValueError(REGISTER_SIZES_MISMATCH_ERROR_MSG)

    def _get_error_msg(self, names: Iterable[IOName], msg: str) -> list[str]:
        bad_names = [name for name in names if re.fullmatch(NAME_REGEX, name) is None]
        return [f"{msg}: {bad_names}"] if bad_names else []

    @classmethod
    def discriminator(cls) -> FunctionParamsDiscriminator:
        return cls.__name__

    model_config = ConfigDict(frozen=True, extra="forbid")


def parse_function_params(
    *,
    params: Any,
    discriminator: Optional[Any],
    param_classes: Collection[type[FunctionParams]],
    no_discriminator_error: Exception,
    bad_function_error: Exception,
    default_parser_class: Optional[type[FunctionParams]] = None,
) -> FunctionParams:  # Any is for use in pydantic validators.
    if not discriminator:
        raise no_discriminator_error

    matching_classes = [
        param_class
        for param_class in param_classes
        if param_class.discriminator() == discriminator
    ]

    if len(matching_classes) != 1:
        if default_parser_class is not None:
            try:
                return default_parser_class.model_validate(params)
            except Exception:
                raise bad_function_error from None
        raise bad_function_error

    return matching_classes[0].model_validate(params)


def parse_function_params_values(
    *,
    values: dict[str, Any],
    params_key: str,
    discriminator_key: str,
    param_classes: Collection[type[FunctionParams]],
    default_parser_class: type[FunctionParams],
) -> None:
    params = values.get(params_key, dict())
    if isinstance(params, FunctionParams):
        values.setdefault(discriminator_key, params.discriminator())
        return
    discriminator = values.get(discriminator_key)
    values[params_key] = parse_function_params(
        params=params,
        discriminator=discriminator,
        param_classes=param_classes,
        no_discriminator_error=ClassiqValueError(
            f"The {discriminator_key} {NO_DISCRIMINATOR_ERROR_MSG} {params_key} type."
        ),
        bad_function_error=ClassiqValueError(
            f"{BAD_FUNCTION_ERROR_MSG} {discriminator_key}: {discriminator}"
        ),
        default_parser_class=default_parser_class,
    )
