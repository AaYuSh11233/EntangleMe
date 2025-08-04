from collections import Counter
from enum import Enum, EnumMeta, IntEnum
from typing import Any, Callable

import pydantic

from classiq.interface.ast_node import HashableASTNode
from classiq.interface.exceptions import ClassiqValueError


def rebuild_dynamic_enum(name: str, members: dict[str, int]) -> type[IntEnum]:
    """
    Rebuilds the dynamic enum from its name and members.
    Returns a new enum type.
    """
    new_enum = IntEnum(name, members)  # type: ignore[misc]
    setattr(new_enum, "__members_data__", members)  # noqa: B010
    setattr(new_enum, "__reduce_ex__", dynamic_enum_reduce_ex)  # noqa: B010
    return new_enum


def dynamic_enum_reduce_ex(
    obj: Any, protocol: int
) -> tuple[Callable[..., type[IntEnum]], tuple[str, dict[str, int]]]:
    """
    Custom __reduce_ex__ for dynamic enums.
    This function will be used when pickling an enum type or one of its members.
    """
    # Get the enum type and its member data.
    enum_type = type(obj)
    members = getattr(enum_type, "__members_data__", None)
    if members is None:
        raise ValueError("Dynamic enum is missing __members_data__ attribute")
    # Return the callable and arguments needed to rebuild the enum type.
    return rebuild_dynamic_enum, (enum_type.__name__, members)


class EnumDeclaration(HashableASTNode):
    name: str

    members: dict[str, int] = pydantic.Field(
        default_factory=dict,
        description="Dictionary of member names and their values",
    )

    @pydantic.field_validator("members")
    @classmethod
    def _validate_members(cls, members: dict[str, int]) -> dict[str, int]:
        underscore_members = [
            member for member in members.keys() if member.startswith("_")
        ]
        if len(underscore_members) > 0:
            raise ClassiqValueError(
                f"Enum member names must not start with an underscore. The offending "
                f"members: {underscore_members}"
            )

        counter = Counter(members.values())
        repeating_members = [
            member for member, value in members.items() if counter[value] > 1
        ]
        if len(repeating_members) > 0:
            raise ClassiqValueError(
                f"Cannot assign the same value to more than one enum member. The "
                f"offending members: {repeating_members}"
            )

        return members

    def create_enum(self) -> type[IntEnum]:
        dynamic_enum = IntEnum(self.name, self.members)  # type: ignore[misc]
        setattr(dynamic_enum, "__members_data__", self.members)  # noqa: B010
        setattr(dynamic_enum, "__reduce_ex__", dynamic_enum_reduce_ex)  # noqa: B010
        return dynamic_enum


def declaration_from_enum(enum_type: EnumMeta) -> EnumDeclaration:
    members = _get_members(enum_type)
    return EnumDeclaration(
        name=enum_type.__name__,
        members={
            member.name: member.value
            for member in sorted(members, key=lambda member: member.value)
        },
    )


def _get_members(enum_type: EnumMeta) -> list[Enum]:
    members: list[Enum] = list(enum_type)
    for member in members:
        if not isinstance(member.value, int):
            raise ClassiqValueError(
                f"Member {member.name!r} of enum {enum_type.__name__!r} has a "
                f"non-integer value {member.value!r}"
            )
    return members
