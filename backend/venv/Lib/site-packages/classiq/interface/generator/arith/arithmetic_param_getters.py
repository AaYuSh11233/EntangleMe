from typing import Callable, Optional

from classiq.interface.exceptions import ClassiqArithmeticError
from classiq.interface.generator.arith.argument_utils import (
    RegisterOrConst as RegisterOrFloat,
)
from classiq.interface.generator.arith.arithmetic_arg_type_validator import (
    validate_operation_arg_types,
)
from classiq.interface.generator.arith.arithmetic_operations import (
    ArithmeticOperationParams,
)
from classiq.interface.generator.arith.ast_node_rewrite import SEPARATOR
from classiq.interface.generator.arith.binary_ops import (
    Adder,
    BitwiseAnd,
    BitwiseOr,
    BitwiseXor,
    CyclicShift,
    Equal,
    GreaterEqual,
    GreaterThan,
    LessEqual,
    LessThan,
    LShift,
    Modulo,
    Multiplier,
    NotEqual,
    Power,
    RegisterOrInt,
    RShift,
    Subtractor,
)
from classiq.interface.generator.arith.extremum_operations import Max, Min
from classiq.interface.generator.arith.logical_ops import LogicalAnd, LogicalOr
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.arith.unary_ops import BitwiseInvert, Negation

ParamsGetter = Callable[..., ArithmeticOperationParams]  # Argument vary

_TARGET_ERROR_MESSAGE: str = "Target unavailable for the requested operation"
_OPERATIONS_ALLOWING_TARGET: frozenset = frozenset(
    {"And", "Or", "Eq", "NotEq", "Lt", "Gt", "LtE", "GtE"}
)


def id2op(node_id: str) -> str:
    return node_id.rsplit(SEPARATOR)[0]


def operation_allows_target(operation: str) -> bool:
    return operation in _OPERATIONS_ALLOWING_TARGET


def get_params(
    *,
    node_id: str,
    args: list[RegisterOrFloat],
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    operation = id2op(node_id)
    if target and not operation_allows_target(operation):
        raise ClassiqArithmeticError(_TARGET_ERROR_MESSAGE)
    validate_operation_arg_types(operation, args, machine_precision)
    return params_getter_map[operation](
        *args,
        machine_precision=machine_precision,
        output_size=output_size,
        inplace_arg=inplace_arg,
        target=target,
    )


def or_params_getter(
    left_arg: RegisterOrInt,
    right_arg: RegisterOrInt,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return BitwiseOr(
        left_arg=left_arg,
        right_arg=right_arg,
        output_size=output_size,
        machine_precision=machine_precision,
    )


def and_params_getter(
    left_arg: RegisterOrInt,
    right_arg: RegisterOrInt,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return BitwiseAnd(
        left_arg=left_arg,
        right_arg=right_arg,
        output_size=output_size,
        machine_precision=machine_precision,
    )


def xor_params_getter(
    left_arg: RegisterOrInt,
    right_arg: RegisterOrInt,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return BitwiseXor(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
        inplace_arg=inplace_arg,
    )


def invert_params_getter(
    arg: RegisterOrInt,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return BitwiseInvert(
        arg=arg,
        machine_precision=machine_precision,
        output_size=output_size,
        inplace=inplace_arg is not None,
    )


def usub_params_getter(
    arg: RegisterOrInt,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Negation(
        arg=arg,
        machine_precision=machine_precision,
        output_size=output_size,
        inplace=inplace_arg is not None,
    )


def adder_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Adder(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def multiplier_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Multiplier(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
    )


def power_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Power(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
    )


def min_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Min(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
    )


def max_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Max(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
    )


def sub_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Subtractor(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def equal_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Equal(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def not_equal_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return NotEqual(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def greater_than_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return GreaterThan(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def greater_equal_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return GreaterEqual(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def less_than_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return LessThan(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def less_equal_params_getter(
    left_arg: RegisterOrFloat,
    right_arg: RegisterOrFloat,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return LessEqual(
        left_arg=left_arg, right_arg=right_arg, machine_precision=machine_precision
    )


def logical_and_params_getter(
    *arg: list[RegisterOrFloat],
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return LogicalAnd(args=arg, target=target, machine_precision=machine_precision)


def logical_or_params_getter(
    *arg: list[RegisterOrFloat],
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return LogicalOr(args=arg, target=target, machine_precision=machine_precision)


def lshift_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return LShift(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def rshift_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return RShift(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def clshift_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return CyclicShift(
        left_arg=left_arg,
        right_arg=-right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def crshift_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return CyclicShift(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        inplace_arg=inplace_arg,
        output_size=output_size,
    )


def modulo_params_getter(
    left_arg: RegisterArithmeticInfo,
    right_arg: int,
    machine_precision: int,
    output_size: Optional[int] = None,
    inplace_arg: Optional[str] = None,
    target: Optional[RegisterArithmeticInfo] = None,
) -> ArithmeticOperationParams:
    return Modulo(
        left_arg=left_arg,
        right_arg=right_arg,
        machine_precision=machine_precision,
        output_size=output_size,
        inplace_arg=inplace_arg,
    )


params_getter_map: dict[str, ParamsGetter] = dict(
    BitOr=or_params_getter,
    BitAnd=and_params_getter,
    BitXor=xor_params_getter,
    Add=adder_params_getter,
    Invert=invert_params_getter,
    Eq=equal_params_getter,
    And=logical_and_params_getter,
    Or=logical_or_params_getter,
    USub=usub_params_getter,
    Sub=sub_params_getter,
    Mult=multiplier_params_getter,
    Gt=greater_than_params_getter,
    GtE=greater_equal_params_getter,
    Lt=less_than_params_getter,
    LtE=less_equal_params_getter,
    NotEq=not_equal_params_getter,
    RShift=rshift_params_getter,
    LShift=lshift_params_getter,
    CRShift=crshift_params_getter,
    CLShift=clshift_params_getter,
    Mod=modulo_params_getter,
    min=min_params_getter,
    max=max_params_getter,
    Pow=power_params_getter,
)
