from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Union

import sympy
from sympy import Integer
from typing_extensions import TypeGuard

from classiq.interface.exceptions import ClassiqIndexError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.model.handle_binding import (
    HandleBinding,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)

if TYPE_CHECKING:
    from classiq.interface.generator.expressions.expression_types import ExpressionValue
    from classiq.interface.generator.functions.concrete_types import (
        ConcreteClassicalType,
    )


def _is_int(val: Any) -> TypeGuard[Union[int, sympy.Basic]]:
    if isinstance(val, AnyClassicalValue):
        return False
    if isinstance(val, sympy.Basic):
        return val.is_Number
    return isinstance(val, int)


class ClassicalSequenceProxy(NonSymbolicExpr, ClassicalProxy):
    def __init__(self, handle: HandleBinding) -> None:
        super().__init__(handle)

    @property
    def fields(self) -> Mapping[str, "ExpressionValue"]:
        return {"len": self.length}

    @property
    def type_name(self) -> str:
        return "Array"

    @property
    def length(self) -> "ExpressionValue":
        raise NotImplementedError

    def __getitem__(
        self, key: Union[slice, int, Integer, ClassicalProxy]
    ) -> ClassicalProxy:
        return (
            self._get_slice(key) if isinstance(key, slice) else self._get_subscript(key)
        )

    def _get_slice(self, slice_: slice) -> ClassicalProxy:
        start_ = slice_.start
        stop_ = slice_.stop
        if _is_int(start_) and _is_int(stop_):
            start = int(start_)
            stop = int(stop_)
            if start > stop:
                raise ClassiqIndexError("Array slice has negative length")
            if start < 0 or (isinstance(self.length, int) and stop > self.length):
                raise ClassiqIndexError("Array slice is out of bounds")
        return self.get_slice_at(start_, stop_)

    def get_slice_at(self, start: Any, stop: Any) -> ClassicalProxy:
        raise NotImplementedError

    def _get_subscript(
        self, index_: Union[int, Integer, ClassicalProxy]
    ) -> ClassicalProxy:
        if _is_int(index_):
            index = int(index_)
            if index < 0:
                raise ClassiqIndexError(
                    "Array index is out of bounds (negative indices are not supported)"
                )
            if isinstance(self.length, int) and index >= self.length:
                raise ClassiqIndexError("Array index is out of bounds")
        if isinstance(index_, tuple):
            raise ClassiqIndexError(
                "list indices must be integers or slices, not tuple"
            )
        return self.get_subscript_at(index_)

    def get_subscript_at(self, index: Any) -> ClassicalProxy:
        raise NotImplementedError


class ClassicalArrayProxy(ClassicalSequenceProxy):
    def __init__(
        self,
        handle: HandleBinding,
        element_type: "ConcreteClassicalType",
        length: "ExpressionValue",
    ) -> None:
        super().__init__(handle)
        self._element_type = element_type
        if _is_int(length):
            length = int(length)
        self._length = length

    @property
    def length(self) -> "ExpressionValue":
        return self._length

    def get_slice_at(self, start: Any, stop: Any) -> ClassicalProxy:
        return ClassicalArrayProxy(
            SlicedHandleBinding(
                base_handle=self.handle,
                start=Expression(expr=str(start)),
                end=Expression(expr=str(stop)),
            ),
            self._element_type,
            stop - start,
        )

    def get_subscript_at(self, index: Any) -> ClassicalProxy:
        return self._element_type.get_classical_proxy(
            SubscriptHandleBinding(
                base_handle=self._handle, index=Expression(expr=str(index))
            )
        )


class ClassicalTupleProxy(ClassicalSequenceProxy):
    def __init__(
        self, handle: HandleBinding, element_types: list["ConcreteClassicalType"]
    ) -> None:
        super().__init__(handle)
        self._element_types = element_types

    @property
    def length(self) -> int:
        return len(self._element_types)

    def get_slice_at(self, start: Any, stop: Any) -> ClassicalProxy:
        handle = SlicedHandleBinding(
            base_handle=self.handle,
            start=Expression(expr=str(start)),
            end=Expression(expr=str(stop)),
        )
        if (_is_int(start) or start is None) and (_is_int(stop) or stop is None):
            return ClassicalTupleProxy(
                handle, self._element_types.__getitem__(slice(start, stop))
            )
        return ClassicalArrayProxy(
            handle,
            self._element_types[0].get_raw_type(),
            stop - start,
        )

    def get_subscript_at(self, index: Any) -> ClassicalProxy:
        handle = SubscriptHandleBinding(
            base_handle=self._handle, index=Expression(expr=str(index))
        )
        if _is_int(index):
            return self._element_types[int(index)].get_classical_proxy(handle)
        return (
            self._element_types[0]
            .get_raw_type()
            .get_classical_proxy(
                SubscriptHandleBinding(
                    base_handle=self._handle, index=Expression(expr=str(index))
                )
            )
        )
