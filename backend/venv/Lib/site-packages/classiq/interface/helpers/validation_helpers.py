from collections.abc import Hashable, Mapping

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.pydantic_model_helpers import Nameable


def is_list_unique(lst: list[Hashable]) -> bool:
    return len(set(lst)) == len(lst)


def validate_nameables_mapping(
    nameables_dict: Mapping[str, Nameable], declaration_type: str
) -> None:
    if not all(name == nameable.name for (name, nameable) in nameables_dict.items()):
        raise ClassiqValueError(
            f"{declaration_type} declaration names should match the keys of their names."
        )
