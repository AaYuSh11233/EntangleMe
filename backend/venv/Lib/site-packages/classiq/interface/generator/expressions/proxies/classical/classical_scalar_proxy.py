from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from sympy import Symbol

from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.model.handle_binding import HandleBinding

if TYPE_CHECKING:
    from classiq.interface.generator.expressions.expression_types import ExpressionValue
    from classiq.interface.generator.functions.classical_type import ClassicalType


class ClassicalScalarProxy(Symbol, ClassicalProxy):
    def __new__(
        cls, handle: HandleBinding, *args: Any, **assumptions: bool
    ) -> "ClassicalScalarProxy":
        return super().__new__(cls, str(handle), **assumptions)

    def __init__(self, handle: HandleBinding, classical_type: "ClassicalType") -> None:
        super().__init__(handle)
        self._classical_type = classical_type

    @property
    def fields(self) -> Mapping[str, "ExpressionValue"]:
        return {}

    @property
    def type_name(self) -> str:
        return type(self._classical_type).__name__
