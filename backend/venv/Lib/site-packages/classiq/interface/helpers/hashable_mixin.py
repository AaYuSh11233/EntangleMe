import itertools
import numbers
from collections.abc import Iterator
from enum import EnumMeta
from typing import Any


def immutable_version(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(immutable_version(elem) for elem in value)
    elif isinstance(value, set):
        return frozenset(immutable_version(elem) for elem in value)
    elif isinstance(value, dict):
        return tuple(sorted(value.items()))
    elif isinstance(value, EnumMeta):
        return tuple(op.name for op in value)  # type:ignore[var-annotated]
    elif isinstance(value, numbers.Number):
        return str(value)
    return value


class HashableMixin:
    def __hash__(self) -> int:
        return hash(self._value_tuple())

    def _values_to_hash(self) -> Iterator[Any]:
        yield from self.__dict__.values()

    def _immutable_fields(self) -> Iterator[Any]:
        for val in self._values_to_hash():
            yield immutable_version(val)

    def _value_tuple(self) -> tuple[Any, ...]:
        return tuple(itertools.chain((str(type(self))), self._immutable_fields()))
