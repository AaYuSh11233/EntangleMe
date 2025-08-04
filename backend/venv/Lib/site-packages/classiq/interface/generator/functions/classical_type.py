from itertools import chain
from typing import TYPE_CHECKING, Any, Literal, Optional

import pydantic
from pydantic import ConfigDict, PrivateAttr
from typing_extensions import Self

from classiq.interface.ast_node import HashableASTNode
from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.expression_types import ExpressionValue
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.expressions.proxies.classical.classical_array_proxy import (
    ClassicalArrayProxy,
    ClassicalTupleProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_scalar_proxy import (
    ClassicalScalarProxy,
)
from classiq.interface.helpers.pydantic_model_helpers import values_with_discriminator
from classiq.interface.model.handle_binding import HandleBinding

if TYPE_CHECKING:
    from classiq.interface.generator.functions.concrete_types import (
        ConcreteClassicalType,
    )


class ClassicalType(HashableASTNode):
    _is_generative: bool = PrivateAttr(default=False)

    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        return str(type(self).__name__)

    def set_generative(self) -> Self:
        self._is_generative = True
        return self

    @property
    def is_generative(self) -> bool:
        return self._is_generative

    @property
    def is_purely_declarative(self) -> bool:
        return not self._is_generative

    @property
    def is_purely_generative(self) -> bool:
        return self._is_generative

    def get_classical_proxy(self, handle: HandleBinding) -> ClassicalProxy:
        return ClassicalScalarProxy(handle, self)

    @property
    def qmod_type_name(self) -> str:
        raise NotImplementedError

    @property
    def raw_qmod_type_name(self) -> str:
        return self.qmod_type_name

    @property
    def expressions(self) -> list[Expression]:
        return []

    def clear_flags(self) -> Self:
        res = self.model_copy()
        res._is_generative = False
        return res

    def get_raw_type(self) -> "ConcreteClassicalType":
        return self  # type:ignore[return-value]


class Integer(ClassicalType):
    kind: Literal["int"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "int")

    @property
    def qmod_type_name(self) -> str:
        return "CInt"


class Real(ClassicalType):
    kind: Literal["real"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "real")

    @property
    def qmod_type_name(self) -> str:
        return "CReal"


class Bool(ClassicalType):
    kind: Literal["bool"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "bool")

    @property
    def qmod_type_name(self) -> str:
        return "CBool"


class StructMetaType(ClassicalType):
    kind: Literal["type_proxy"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "type_proxy")

    def get_classical_proxy(self, handle: HandleBinding) -> ClassicalProxy:
        raise NotImplementedError


class ClassicalArray(ClassicalType):
    kind: Literal["array"]
    element_type: "ConcreteClassicalType"
    length: Optional[Expression] = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "array")

    @property
    def has_length(self) -> bool:
        return self.length is not None and self.length.is_evaluated()

    @property
    def length_value(self) -> int:
        if not self.has_length:
            raise ClassiqInternalExpansionError(
                "Tried to access unevaluated length of classical array"
            )
        assert self.length is not None
        return self.length.to_int_value()

    def get_classical_proxy(self, handle: HandleBinding) -> ClassicalProxy:
        length: ExpressionValue
        if self.length is None:
            length = AnyClassicalValue(f"get_field({handle}, 'len')")
        elif not self.length.is_evaluated():
            raise ClassiqInternalExpansionError(
                "Classical list length is not evaluated"
            )
        else:
            length = self.length.value.value
        return ClassicalArrayProxy(handle, self.element_type, length)

    @property
    def expressions(self) -> list[Expression]:
        return self.element_type.expressions

    @property
    def is_purely_declarative(self) -> bool:
        return super().is_purely_declarative and self.element_type.is_purely_declarative

    @property
    def is_purely_generative(self) -> bool:
        return super().is_purely_generative and self.element_type.is_purely_generative

    def get_raw_type(self) -> "ConcreteClassicalType":
        raw_type = ClassicalArray(element_type=self.element_type.get_raw_type())
        if self._is_generative:
            raw_type.set_generative()
        return raw_type

    @property
    def qmod_type_name(self) -> str:
        if self.length is None:
            length = ""
        else:
            length = f", {self.length.expr}"
        return f"CArray[{self.element_type.qmod_type_name}{length}]"

    @property
    def raw_qmod_type_name(self) -> str:
        return "CArray"


class ClassicalTuple(ClassicalType):
    kind: Literal["tuple"]
    element_types: list["ConcreteClassicalType"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "tuple")

    def get_classical_proxy(self, handle: HandleBinding) -> ClassicalProxy:
        return ClassicalTupleProxy(handle=handle, element_types=self.element_types)

    @property
    def expressions(self) -> list[Expression]:
        return list(
            chain.from_iterable(
                element_type.expressions for element_type in self.element_types
            )
        )

    @property
    def is_purely_declarative(self) -> bool:
        return super().is_purely_declarative and all(
            element_type.is_purely_declarative for element_type in self.element_types
        )

    @property
    def is_purely_generative(self) -> bool:
        return super().is_purely_generative and all(
            element_type.is_purely_generative for element_type in self.element_types
        )

    def get_raw_type(self, *, preserve_length: bool = False) -> "ConcreteClassicalType":
        if len(self.element_types) == 0:
            return self
        chosen_element = self.element_types[0]
        for element in self.element_types:
            if (
                not isinstance(element, ClassicalTuple)
                or len(element.element_types) > 0
            ):
                chosen_element = element
                break
        if preserve_length:
            length = Expression(expr=str(len(self.element_types)))
        else:
            length = None
        raw_type = ClassicalArray(
            element_type=chosen_element.get_raw_type(), length=length
        )
        if self._is_generative:
            raw_type.set_generative()
        return raw_type

    @property
    def length(self) -> int:
        return len(self.element_types)

    @property
    def qmod_type_name(self) -> str:
        raw_type = self.get_raw_type(preserve_length=True)
        if isinstance(raw_type, ClassicalTuple):
            return "CArray[0]"
        return raw_type.qmod_type_name

    @property
    def raw_qmod_type_name(self) -> str:
        return "CArray"


class OpaqueHandle(ClassicalType):
    pass


class VQEResult(OpaqueHandle):
    kind: Literal["vqe_result"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "vqe_result")


class Histogram(OpaqueHandle):
    kind: Literal["histogram"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "histogram")


class Estimation(OpaqueHandle):
    kind: Literal["estimation_result"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "estimation_result")


class IQAERes(OpaqueHandle):
    kind: Literal["iqae_result"]

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "iqae_result")


class QmodPyObject:
    pass


CLASSICAL_ATTRIBUTES_TYPES = {
    "len": Integer(),
    "size": Integer(),
    "is_signed": Bool(),
    "fraction_digits": Integer(),
}
