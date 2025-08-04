from collections.abc import Mapping
from typing import TYPE_CHECKING

from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.model.handle_binding import FieldHandleBinding, HandleBinding

if TYPE_CHECKING:
    from classiq.interface.generator.expressions.expression_types import ExpressionValue
    from classiq.interface.generator.types.struct_declaration import StructDeclaration


class ClassicalStructProxy(NonSymbolicExpr, ClassicalProxy):
    def __init__(self, handle: HandleBinding, decl: "StructDeclaration") -> None:
        super().__init__(handle)
        self._decl = decl

    @property
    def struct_declaration(self) -> "StructDeclaration":
        return self._decl

    @property
    def fields(self) -> Mapping[str, "ExpressionValue"]:
        return {
            field_name: field_type.get_classical_proxy(
                FieldHandleBinding(base_handle=self.handle, field=field_name)
            )
            for field_name, field_type in self._decl.variables.items()
        }

    @property
    def type_name(self) -> str:
        return f"Struct {self._decl.name}"
