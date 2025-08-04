from collections.abc import Sequence
from typing import Any, Protocol, TypeVar


def values_with_discriminator(
    values: Any, discriminator: str, discriminator_value: Any
) -> dict[str, Any]:
    if isinstance(values, dict):
        values.setdefault(discriminator, discriminator_value)
    return values


class Nameable(Protocol):
    name: str


NameableType = TypeVar("NameableType", bound=Nameable)


def nameables_to_dict(nameables: Sequence[NameableType]) -> dict[str, NameableType]:
    return {value.name: value for value in nameables}
