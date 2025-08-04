from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classiq.interface.generator.expressions.expression_types import ExpressionValue
    from classiq.interface.model.handle_binding import HandleBinding


class ClassicalProxy:
    def __init__(self, handle: "HandleBinding") -> None:
        self._handle = handle

    @property
    def handle(self) -> "HandleBinding":
        return self._handle

    def __str__(self) -> str:
        return str(self.handle)

    @property
    def fields(self) -> Mapping[str, "ExpressionValue"]:
        raise NotImplementedError

    @property
    def type_name(self) -> str:
        raise NotImplementedError
