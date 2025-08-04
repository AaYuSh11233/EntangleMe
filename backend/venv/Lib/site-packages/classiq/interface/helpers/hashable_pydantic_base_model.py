from collections.abc import Collection, Iterator
from typing import Any

import pydantic

from classiq.interface.helpers.hashable_mixin import HashableMixin


class HashablePydanticBaseModel(HashableMixin, pydantic.BaseModel):
    _fields_to_skip_in_hash: Collection[str] = pydantic.PrivateAttr(default_factory=set)

    def _values_to_hash(self) -> Iterator[Any]:
        for field, value in self.__dict__.items():
            if field in self._fields_to_skip_in_hash:
                continue
            yield value

    def __hash__(self) -> int:  # taken from pydantic.BaseModel otherwise
        return HashableMixin.__hash__(self)
