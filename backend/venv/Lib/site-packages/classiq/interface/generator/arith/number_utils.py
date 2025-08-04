from typing import Final, Union

MAXIMAL_MACHINE_PRECISION: Final[int] = 20


def signed_int_to_unsigned(number: int) -> int:
    """Return the integer value of a signed int if it would we read as un-signed in binary representation"""
    if number >= 0:
        return number

    not_power2 = abs(number) & (abs(number) - 1) != 0
    return number + 2 ** (number.bit_length() + 1 * not_power2)


def binary_to_int(bin_rep: str, is_signed: bool = False) -> int:
    negative_offset: int = -(2 ** len(bin_rep)) * (bin_rep[0] == "1") * is_signed
    return int(bin_rep, 2) + negative_offset


def binary_to_float(
    bin_rep: str, fraction_part_size: int = 0, is_signed: bool = False
) -> float:
    return binary_to_int(bin_rep, is_signed) / 2**fraction_part_size


def binary_to_float_or_int(
    bin_rep: str, fraction_part_size: int = 0, is_signed: bool = False
) -> Union[float, int]:
    if fraction_part_size == 0:
        return binary_to_int(bin_rep, is_signed)
    return binary_to_float(bin_rep, fraction_part_size, is_signed)


def _get_fraction_places(*, binary_value: str) -> int:
    fraction_places = MAXIMAL_MACHINE_PRECISION
    for bit in reversed(binary_value):
        if bit == "1" or fraction_places == 0:
            return fraction_places
        fraction_places -= 1
    return fraction_places


def get_int_representation_and_fraction_places(float_value: float) -> tuple[int, int]:
    int_val = signed_int_to_unsigned(int(float_value * 2**MAXIMAL_MACHINE_PRECISION))
    if int_val == 0:
        return 0, 0
    fraction_places = _get_fraction_places(binary_value=bin(int_val)[2:])
    int_val = int_val >> (MAXIMAL_MACHINE_PRECISION - fraction_places)
    return int_val, fraction_places


def fraction_places(float_value: float) -> int:
    int_val = signed_int_to_unsigned(int(float_value * 2**MAXIMAL_MACHINE_PRECISION))
    if int_val == 0:
        return 0
    return _get_fraction_places(binary_value=bin(int_val)[2:])


def _bit_length(integer_representation: int) -> int:
    return 1 if integer_representation == 0 else integer_representation.bit_length()


def binary_string(float_value: float) -> str:
    int_val, _ = get_int_representation_and_fraction_places(float_value)
    bin_rep = bin(int_val)[2:]
    size_diff = size(float_value=float_value) - len(bin_rep)
    extension_bit = "0" if float_value >= 0 else "1"
    return bin_rep[::-1] + extension_bit * size_diff


def integer_part_size(float_value: float) -> int:
    int_val, fraction_places = get_int_representation_and_fraction_places(float_value)
    return max(_bit_length(int_val) - fraction_places, 0)


def size(float_value: float) -> int:
    int_val, fraction_places = get_int_representation_and_fraction_places(float_value)
    return max(_bit_length(int_val), fraction_places)


def _is_extra_sign_bit_needed(*, lb: float, ub: float) -> bool:
    fractions = max(fraction_places(lb), fraction_places(ub))
    integer_lb = lb * 2**fractions
    max_represented_number = (
        2 ** (len(binary_string(integer_lb)) - 1) - 1
    ) / 2**fractions
    return ub > max_represented_number


def bounds_to_integer_part_size(lb: float, ub: float) -> int:
    lb, ub = min(lb, ub), max(lb, ub)
    ub_integer_part_size: int = integer_part_size(float_value=ub)
    lb_integer_part_size: int = integer_part_size(float_value=lb)
    if lb >= 0:
        return ub_integer_part_size
    if ub <= 0:
        return lb_integer_part_size
    return max(
        ub_integer_part_size + 1 * _is_extra_sign_bit_needed(lb=lb, ub=ub),
        lb_integer_part_size,
    )


def bounds_to_attributes(
    lb: float, ub: float, fraction_places: int, machine_precision: int
) -> tuple[int, bool, int]:
    fraction_places = min(fraction_places, machine_precision)
    if lb == ub == 0:
        integers = 0
    else:
        integers = bounds_to_integer_part_size(lb, ub)
    return max(1, integers + fraction_places), lb < 0, fraction_places


def limit_fraction_places(number: float, machine_precision: int) -> float:
    orig_bin_rep = binary_string(number)[::-1]
    orig_fractions = fraction_places(number)

    removed_fractions = max(orig_fractions - machine_precision, 0)
    return binary_to_float(
        bin_rep=orig_bin_rep[: len(orig_bin_rep) - removed_fractions],
        fraction_part_size=orig_fractions - removed_fractions,
        is_signed=number < 0,
    )


def bounds_cut(
    bounds1: tuple[float, float], bounds2: tuple[float, float]
) -> tuple[float, float]:
    return max(min(bounds1), min(bounds2)), min(max(bounds1), max(bounds2))
