from collections.abc import Mapping
from itertools import chain
from typing import TYPE_CHECKING, Any, Literal, Optional

import pydantic

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_scalar_proxy import (
    ClassicalScalarProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_struct_proxy import (
    ClassicalStructProxy,
)
from classiq.interface.generator.expressions.proxies.quantum.qmod_qstruct_proxy import (
    QmodQStructProxy,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalType,
)
from classiq.interface.helpers.pydantic_model_helpers import values_with_discriminator
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_type import (
    QuantumType,
)

if TYPE_CHECKING:
    from classiq.interface.generator.functions.concrete_types import (
        ConcreteClassicalType,
        ConcreteQuantumType,
    )
    from classiq.interface.generator.types.struct_declaration import StructDeclaration


class TypeName(ClassicalType, QuantumType):
    kind: Literal["struct_instance"]
    name: str = pydantic.Field(description="The type name of the instance")
    _assigned_fields: Optional[Mapping[str, "ConcreteQuantumType"]] = (
        pydantic.PrivateAttr(default=None)
    )
    _classical_struct_decl: Optional["StructDeclaration"] = pydantic.PrivateAttr(
        default=None
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "struct_instance")

    def _update_size_in_bits_from_declaration(self) -> None:
        fields_types = list(self.fields.values())
        for field_type in fields_types:
            field_type._update_size_in_bits_from_declaration()
        if all(field_type.has_size_in_bits for field_type in fields_types):
            self._size_in_bits = sum(
                field_type.size_in_bits for field_type in fields_types
            )

    def get_proxy(self, handle: "HandleBinding") -> "QmodQStructProxy":
        from classiq.interface.generator.expressions.proxies.quantum.qmod_qstruct_proxy import (
            QmodQStructProxy,
        )

        return QmodQStructProxy(
            handle=handle, struct_name=self.name, fields=self.fields
        )

    @property
    def qmod_type_name(self) -> str:
        return self.name

    @property
    def type_name(self) -> str:
        return self.name

    @property
    def fields(self) -> Mapping[str, "ConcreteQuantumType"]:
        if self._assigned_fields is None:
            raise ClassiqExpansionError(f"Type {self.name!r} is undefined")
        return self._assigned_fields

    @property
    def has_fields(self) -> bool:
        return self._assigned_fields is not None

    def set_fields(self, fields: Mapping[str, "ConcreteQuantumType"]) -> None:
        self._assigned_fields = fields

    @property
    def is_instantiated(self) -> bool:
        return self.has_fields and all(
            field_type.is_instantiated for field_type in self.fields.values()
        )

    @property
    def is_evaluated(self) -> bool:
        return self.has_fields and all(
            field_type.is_evaluated for field_type in self.fields.values()
        )

    @property
    def has_classical_struct_decl(self) -> bool:
        return self._classical_struct_decl is not None

    @property
    def classical_struct_decl(self) -> "StructDeclaration":
        if self._classical_struct_decl is None:
            raise ClassiqExpansionError(f"Type {self.name!r} is undefined")
        return self._classical_struct_decl

    def set_classical_struct_decl(self, decl: "StructDeclaration") -> None:
        self._classical_struct_decl = decl

    def get_classical_proxy(self, handle: HandleBinding) -> ClassicalProxy:
        if self.is_enum:
            return ClassicalScalarProxy(handle, self)
        if TYPE_CHECKING:
            assert self._classical_struct_decl is not None
        return ClassicalStructProxy(handle, self._classical_struct_decl)

    @property
    def expressions(self) -> list[Expression]:
        if self.has_fields:
            return list(
                chain.from_iterable(
                    field_type.expressions for field_type in self.fields.values()
                )
            )
        if self.has_classical_struct_decl:
            return list(
                chain.from_iterable(
                    field_type.expressions
                    for field_type in self.classical_struct_decl.variables.values()
                )
            )
        return []

    @property
    def is_purely_declarative(self) -> bool:
        if self.is_enum:
            return not self.is_generative
        return all(
            field_type.is_purely_declarative
            for field_type in self.classical_struct_decl.variables.values()
        )

    @property
    def is_purely_generative(self) -> bool:
        if self.is_enum:
            return self.is_generative
        return all(
            field_type.is_purely_generative
            for field_type in self.classical_struct_decl.variables.values()
        )

    @property
    def is_enum(self) -> bool:
        return not self.has_fields and not self.has_classical_struct_decl

    def get_raw_type(self) -> "ConcreteClassicalType":
        if self.is_enum:
            return self
        if TYPE_CHECKING:
            assert self._classical_struct_decl is not None
        raw_type = TypeName(name=self.name)
        raw_decl = self._classical_struct_decl.model_copy(
            update=dict(
                variables={
                    field_name: field_type.get_raw_type()
                    for field_name, field_type in self._classical_struct_decl.variables.items()
                }
            )
        )
        raw_type.set_classical_struct_decl(raw_decl)
        return raw_type

    @property
    def minimal_size_in_bits(self) -> int:
        return sum(
            field_type.minimal_size_in_bits for field_type in self.fields.values()
        )


class Enum(TypeName):
    pass


class Struct(TypeName):
    pass
