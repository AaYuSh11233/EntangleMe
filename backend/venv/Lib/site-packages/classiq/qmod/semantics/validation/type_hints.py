from typing import Any

from typing_extensions import _AnnotatedAlias

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier


def validate_annotation(type_hint: Any) -> None:
    if not isinstance(type_hint, _AnnotatedAlias):
        return
    directions: list[PortDeclarationDirection] = [
        direction
        for direction in type_hint.__metadata__
        if isinstance(direction, PortDeclarationDirection)
    ]
    modifiers: list[TypeModifier] = [
        modifier
        for modifier in type_hint.__metadata__
        if isinstance(modifier, TypeModifier)
    ]
    if len(directions) <= 1 and len(modifiers) <= 1:
        return
    error_message = ""
    if len(directions) > 1:
        error_message += (
            f"Multiple directions are not allowed in a single type hint: "
            f"[{', '.join(direction.name for direction in reversed(directions))}]\n"
        )
    if len(modifiers) > 1:
        error_message += (
            f"Multiple modifiers are not allowed in a single type hint: "
            f"[{', '.join(modifier.name for modifier in reversed(modifiers))}]\n"
        )
    raise ClassiqValueError(error_message)
