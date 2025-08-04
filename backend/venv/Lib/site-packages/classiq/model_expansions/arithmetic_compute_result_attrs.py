import math
from collections.abc import Sequence
from typing import Union

from classiq.interface.exceptions import ClassiqValueError

from classiq.model_expansions.arithmetic import NumericAttributes


def compute_result_attrs_assign(
    source: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    if machine_precision >= source.fraction_digits:
        return source

    trimmed_digits = source.fraction_digits - machine_precision
    return NumericAttributes(
        size=source.size - trimmed_digits,
        is_signed=source.is_signed,
        fraction_digits=machine_precision,
        bounds=source.bounds,
        trim_bounds=True,
    )


def compute_result_attrs_bitwise_invert(
    arg: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    fraction_digits = min(arg.fraction_digits, machine_precision)
    trimmed_bits = arg.fraction_digits - fraction_digits
    return NumericAttributes(
        size=arg.size - trimmed_bits,
        is_signed=arg.is_signed,
        fraction_digits=fraction_digits,
    )


def compute_result_attrs_negate(
    arg: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    lb = -arg.ub
    ub = -arg.lb

    if arg.size == 1:
        return NumericAttributes(
            size=1,
            is_signed=lb < 0,
            fraction_digits=arg.fraction_digits,
            bounds=(lb, ub),
        )
    else:
        return NumericAttributes.from_bounds(
            lb, ub, arg.fraction_digits, machine_precision
        )


def compute_result_attrs_bitwise_and(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    if left.fraction_digits > 0 or right.fraction_digits > 0:
        raise ClassiqValueError("Bitwise AND is only defined for integers")

    # we comply with python, which uses arbitrary precision, so a positive number can
    # always be represented by "0..." and a negative number by "1...", thus their
    # bitwise AND is always non-negative
    return NumericAttributes(
        size=max(left.size, right.size),
        is_signed=left.is_signed and right.is_signed,
        fraction_digits=0,
    )


def compute_result_attrs_bitwise_or(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    if left.fraction_digits > 0 or right.fraction_digits > 0:
        raise ClassiqValueError("Bitwise OR is only defined for integers")

    # we comply with python, which uses arbitrary precision, so a positive number can
    # always be represented by "0..." and a negative number by "1...", thus their
    # bitwise OR is always negative

    if left.is_signed and not right.is_signed:
        # we need to extend right so its MSB is always 0
        size = max(left.size, right.size + 1)
    elif not left.is_signed and right.is_signed:
        # we need to extend left so its MSB is always 0
        size = max(left.size + 1, right.size)
    else:
        size = max(left.size, right.size)

    return NumericAttributes(
        size=size,
        is_signed=left.is_signed or right.is_signed,
        fraction_digits=0,
    )


def compute_result_attrs_bitwise_xor(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    if left.fraction_digits > 0 or right.fraction_digits > 0:
        raise ClassiqValueError("Bitwise XOR is only defined for integers")
    return compute_result_attrs_bitwise_or(left, right, machine_precision)


def compute_result_attrs_add(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    lb = left.lb + right.lb
    ub = left.ub + right.ub
    fraction_places = max(left.fraction_digits, right.fraction_digits)
    return NumericAttributes.from_bounds(lb, ub, fraction_places, machine_precision)


def compute_result_attrs_subtract(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    tmp = compute_result_attrs_negate(right, machine_precision)
    return compute_result_attrs_add(left, tmp, machine_precision)


def compute_result_attrs_multiply(
    left: NumericAttributes,
    right: NumericAttributes,
    machine_precision: int,
) -> NumericAttributes:
    extremal_values = [
        left_val * right_val for left_val in left.bounds for right_val in right.bounds
    ]
    fraction_places = left.fraction_digits + right.fraction_digits
    return NumericAttributes.from_bounds(
        min(extremal_values),
        max(extremal_values),
        fraction_places,
        machine_precision,
        trim_bounds=True,
    )


def compute_result_attrs_power(
    left: NumericAttributes,
    right: Union[int, float],
    machine_precision: int,
) -> NumericAttributes:
    if not float(right).is_integer() or right <= 0:
        raise ClassiqValueError("Power must be a positive integer")
    right = int(right)

    bounds: tuple[float, float]
    if (right % 2 == 0) and (left.lb < 0 < left.ub):
        bounds = (0, max(left.lb**right, left.ub**right))
    else:
        extremal_values = (left.lb**right, left.ub**right)
        bounds = (min(extremal_values), max(extremal_values))
    fraction_places = left.fraction_digits * right
    return NumericAttributes.from_bounds(
        bounds[0], bounds[1], fraction_places, machine_precision, trim_bounds=True
    )


def compute_result_attrs_lshift(
    left: NumericAttributes,
    right: Union[int, float],
    machine_precision: int,
) -> NumericAttributes:
    if not float(right).is_integer() or right < 0:
        raise ClassiqValueError("Shift must be a non-negative integer")
    right = int(right)

    scale = 1 << left.fraction_digits
    lb = (int(left.lb * scale) << right) / scale
    ub = (int(left.ub * scale) << right) / scale
    fraction_digits = max(left.fraction_digits - right, 0)
    integer_digits = left.integer_digits + right
    return NumericAttributes(
        size=integer_digits + fraction_digits,
        is_signed=left.is_signed,
        fraction_digits=fraction_digits,
        bounds=(lb, ub),
    )


def compute_result_attrs_rshift(
    left: NumericAttributes,
    right: Union[int, float],
    machine_precision: int,
) -> NumericAttributes:
    if not float(right).is_integer() or right < 0:
        raise ClassiqValueError("Shift must be a non-negative integer")
    right = int(right)

    scale = 1 << left.fraction_digits
    lb = (int(left.lb * scale) >> right) / scale
    ub = (int(left.ub * scale) >> right) / scale
    fraction_digits = (
        0 if (right >= left.size and not left.is_signed) else left.fraction_digits
    )
    return NumericAttributes(
        size=max(left.size - right, fraction_digits, 1),
        is_signed=left.is_signed,
        fraction_digits=fraction_digits,
        bounds=(lb, ub),
    )


def compute_result_attrs_modulo(
    left: NumericAttributes,
    right: Union[int, float],
    machine_precision: int,
) -> NumericAttributes:
    if not float(right).is_integer() or right < 2:
        raise ClassiqValueError("Modulus must be a positive power of two")
    right = int(right)
    if right & (right - 1) != 0:
        raise ClassiqValueError("Modulus must be a positive power of two")

    if left.fraction_digits > 0:
        raise ClassiqValueError("Modulo is supported for integers only")

    size = int(math.log2(right))
    if not left.is_signed and size >= left.size:
        return left

    return NumericAttributes(
        size=size,
        fraction_digits=0,
        is_signed=False,
    )


def compute_result_attrs_min(
    args: Sequence[NumericAttributes],
    machine_precision: int,
) -> NumericAttributes:
    if len(args) < 1:
        raise ClassiqValueError("Min expects at least one argument")

    args = [arg.trim_fraction_digits(machine_precision) for arg in args]

    result_attrs = args[0]
    for attrs in args[1:]:
        if result_attrs.lb == result_attrs.ub == attrs.lb == attrs.ub:
            if attrs.size < result_attrs.size:
                result_attrs = attrs
        elif result_attrs.ub <= attrs.lb:
            pass
        elif attrs.ub <= result_attrs.lb:
            result_attrs = attrs
        else:
            integer_digits = max(result_attrs.integer_digits, attrs.integer_digits)
            fraction_digits = max(result_attrs.fraction_digits, attrs.fraction_digits)
            bounds = (min(result_attrs.lb, attrs.lb), min(result_attrs.ub, attrs.ub))
            result_attrs = NumericAttributes(
                size=integer_digits + fraction_digits,
                is_signed=bounds[0] < 0,
                fraction_digits=fraction_digits,
                bounds=bounds,
            )

    return result_attrs


def compute_result_attrs_max(
    args: Sequence[NumericAttributes],
    machine_precision: int,
) -> NumericAttributes:
    if len(args) < 1:
        raise ClassiqValueError("Max expects at least one argument")

    args = [arg.trim_fraction_digits(machine_precision) for arg in args]

    result_attrs = args[0]
    for attrs in args[1:]:
        if result_attrs.lb == result_attrs.ub == attrs.lb == attrs.ub:
            if attrs.size < result_attrs.size:
                result_attrs = attrs
        elif result_attrs.lb >= attrs.ub:
            pass
        elif attrs.lb >= result_attrs.ub:
            result_attrs = attrs
        else:
            integer_digits = max(result_attrs.integer_digits, attrs.integer_digits)
            fraction_digits = max(result_attrs.fraction_digits, attrs.fraction_digits)
            bounds = (max(result_attrs.lb, attrs.lb), max(result_attrs.ub, attrs.ub))
            result_attrs = NumericAttributes(
                size=integer_digits + fraction_digits,
                is_signed=bounds[0] < 0,
                fraction_digits=fraction_digits,
                bounds=bounds,
            )

    return result_attrs


def compute_result_attrs_quantum_subscript(
    values: Sequence[float],
    machine_precision: int,
) -> NumericAttributes:
    if len(values) < 1:
        raise ClassiqValueError("Quantum subscript expects at least one argument")

    values_attrs = [
        NumericAttributes.from_constant(val, machine_precision) for val in values
    ]
    values = [attrs.lb for attrs in values_attrs]
    fraction_digits = max(attrs.fraction_digits for attrs in values_attrs)
    return NumericAttributes.from_bounds(
        min(values),
        max(values),
        fraction_digits,
        machine_precision,
    )
