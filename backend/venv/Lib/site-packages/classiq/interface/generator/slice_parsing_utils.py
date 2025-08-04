import re
from re import Match
from typing import Optional

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.function_params import NAME_REGEX

NAME = "name"
SLICING = "slicing"
SEPARATOR = ":"
SLICING_CHARS = rf"[0-9\-{SEPARATOR}]+"
IO_REGEX = rf"(?P<{NAME}>{NAME_REGEX})(\[(?P<{SLICING}>{SLICING_CHARS})\])?"


def parse_io_slicing(io_str: str) -> tuple[str, slice]:
    name, slicing = separate_name_and_slice(io_str)
    return name, get_slice(slicing)


def separate_name_and_slice(io_str: str) -> tuple[str, Optional[str]]:
    match: Optional[Match] = re.fullmatch(IO_REGEX, io_str)
    if match is None:
        raise AssertionError("Input/output name validation error")
    name, slicing = (match.groupdict().get(x) for x in [NAME, SLICING])
    if name is None:
        raise AssertionError("Input/output name validation error")
    return name, slicing


def get_slice(slicing: Optional[str]) -> slice:
    if slicing is None:
        return slice(None)

    split = slicing.split(":")

    if len(split) == 1:
        index_block = split[0]
        try:
            index = int(index_block)
        except ValueError:
            raise ClassiqValueError(
                f"Index {index_block!r} is not an integer"
            ) from None
        stop = index + 1 if index != -1 else None
        return slice(index, stop, None)

    elif len(split) == 2:
        start_block, stop_block = split
        start = _int_or_none(start_block)
        stop = _int_or_none(stop_block)
        return slice(start, stop, None)

    elif len(split) == 3:
        start_block, stop_block, step_block = split
        start = _int_or_none(start_block)
        stop = _int_or_none(stop_block)
        step = _int_or_none(step_block)
        return slice(start, stop, step)

    else:
        raise AssertionError("Input/output slicing validation error")


def _int_or_none(v: str) -> Optional[int]:
    return int(v) if v else None
