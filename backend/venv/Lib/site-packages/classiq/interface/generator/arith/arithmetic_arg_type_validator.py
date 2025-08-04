from typing import Callable

from typing_extensions import TypeAlias

from classiq.interface.exceptions import ClassiqArithmeticError
from classiq.interface.generator.arith import argument_utils
from classiq.interface.generator.arith.binary_ops import BOOLEAN_OP_WITH_FRACTIONS_ERROR

ArgTypeValidator: TypeAlias = Callable[[list[argument_utils.RegisterOrConst]], None]


def _validate_bitwise_op_args(args: list[argument_utils.RegisterOrConst]) -> None:
    if any(argument_utils.fraction_places(arg) > 0 for arg in args):
        raise ClassiqArithmeticError(BOOLEAN_OP_WITH_FRACTIONS_ERROR)


arg_type_validator_map: dict[str, ArgTypeValidator] = dict(
    BitXor=_validate_bitwise_op_args,
    BitAnd=_validate_bitwise_op_args,
    BitOr=_validate_bitwise_op_args,
)


def validate_operation_arg_types(
    operation: str,
    arguments: list[argument_utils.RegisterOrConst],
    machine_precision: int,
) -> None:
    if operation not in arg_type_validator_map:
        return
    limited_args = [
        argument_utils.limit_fraction_places(arg, machine_precision=machine_precision)
        for arg in arguments
    ]
    arg_type_validator_map[operation](limited_args)
