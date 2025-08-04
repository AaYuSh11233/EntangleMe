from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Union

import sympy

if TYPE_CHECKING:
    from classiq.interface.model.handle_binding import HandleBinding


class QmodSizedProxy:
    def __init__(self, handle: "HandleBinding", size: Union[int, sympy.Basic]) -> None:
        self._handle = handle
        self._size = size

    @property
    def size(self) -> Union[int, sympy.Basic]:
        return self._size

    def __str__(self) -> str:
        return self.handle.qmod_expr

    def __repr__(self) -> str:
        return str(self)

    @property
    def type_name(self) -> str:
        raise NotImplementedError

    @property
    def handle(self) -> "HandleBinding":
        return self._handle

    @property
    def len(self) -> int:
        return self._size

    @property
    def fields(self) -> Mapping[str, Any]:
        return {"size": self._size}
