from collections.abc import Iterable
from typing import Union

EXCITATIONS_TYPE = Union[str, int, Iterable[int], Iterable[str]]
EXCITATIONS_TYPE_EXACT = list[int]
