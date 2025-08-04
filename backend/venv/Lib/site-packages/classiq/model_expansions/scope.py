import itertools
from collections import UserDict
from collections.abc import Iterator
from dataclasses import dataclass
from functools import singledispatch
from typing import TYPE_CHECKING, Any, NoReturn, Optional, TypeVar, Union

import sympy

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.evaluated_expression import (
    EvaluatedExpression,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.classical_scalar_proxy import (
    ClassicalScalarProxy,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import ClassicalType
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.helpers.text_utils import readable_list, s
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    GeneralHandle,
    HandleBinding,
    HandlesList,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.quantum_function_call import ArgValue
from classiq.interface.model.quantum_function_declaration import (
    AnonPositionalArg,
    AnonQuantumOperandDeclaration,
)
from classiq.interface.model.quantum_type import (
    QuantumBitvector,
    QuantumNumeric,
    QuantumType,
)

if TYPE_CHECKING:
    from classiq.model_expansions.closure import FunctionClosure

T = TypeVar("T")


@dataclass(frozen=True)
class QuantumVariable:
    quantum_type: QuantumType

    def emit(self) -> GeneralHandle:
        raise NotImplementedError


@dataclass(frozen=True)
class QuantumSymbol(QuantumVariable):
    handle: HandleBinding

    @property
    def is_subscript(self) -> bool:
        return isinstance(self.handle, (SubscriptHandleBinding, SlicedHandleBinding))

    def emit(self) -> HandleBinding:
        return self.handle

    def __getitem__(
        self, item: Union[slice, int, ClassicalScalarProxy]
    ) -> "QuantumSymbol":
        if isinstance(item, slice):
            return self._slice(item.start, item.stop)
        return self._subscript(item)

    def _slice(
        self,
        start: Union[int, ClassicalScalarProxy],
        end: Union[int, ClassicalScalarProxy],
    ) -> "QuantumSymbol":
        if not isinstance(self.quantum_type, QuantumBitvector):
            raise ClassiqExpansionError(
                f"{self.quantum_type.type_name} is not subscriptable"
            )
        if isinstance(start, int) and isinstance(end, int) and start >= end:
            raise ClassiqExpansionError(
                f"{self.quantum_type.type_name} slice '{self.handle}[{start}:{end}]' "
                f"has non-positive length"
            )
        if (isinstance(start, int) and start < 0) or (
            isinstance(end, int)
            and self.quantum_type.length is not None
            and self.quantum_type.length.is_constant()
            and end > self.quantum_type.length_value
        ):
            raise ClassiqExpansionError(
                f"Slice [{start}:{end}] is out of bounds for "
                f"{self.quantum_type.type_name.lower()} {str(self.handle)!r} (of "
                f"length {self.quantum_type.length_value})"
            )
        return QuantumSymbol(
            handle=SlicedHandleBinding(
                base_handle=self.handle,
                start=Expression(expr=str(start)),
                end=Expression(expr=str(end)),
            ),
            quantum_type=QuantumBitvector(
                element_type=self.quantum_type.element_type,
                length=Expression(expr=str(end - start)),
            ),
        )

    def _subscript(self, index: Union[int, ClassicalScalarProxy]) -> "QuantumSymbol":
        if not isinstance(self.quantum_type, QuantumBitvector):
            raise ClassiqExpansionError(
                f"{self.quantum_type.type_name} is not subscriptable"
            )
        if isinstance(index, int) and (
            index < 0
            or (
                self.quantum_type.length is not None
                and self.quantum_type.length.is_constant()
                and index >= self.quantum_type.length_value
            )
        ):
            length_suffix = (
                f" (of length {self.quantum_type.length})"
                if self.quantum_type.length is not None
                else ""
            )
            raise ClassiqExpansionError(
                f"Index {index} is out of bounds for "
                f"{self.quantum_type.type_name.lower()} {str(self.handle)!r}"
                f"{length_suffix}"
            )
        return QuantumSymbol(
            handle=SubscriptHandleBinding(
                base_handle=self.handle,
                index=Expression(expr=str(index)),
            ),
            quantum_type=self.quantum_type.element_type,
        )

    @property
    def fields(self) -> dict[str, "QuantumSymbol"]:
        quantum_type = self.quantum_type
        if not isinstance(quantum_type, TypeName):
            raise ClassiqExpansionError(
                f"{self.quantum_type.type_name} is not a struct"
            )
        return {
            field_name: QuantumSymbol(
                handle=FieldHandleBinding(base_handle=self.handle, field=field_name),
                quantum_type=field_type,
            )
            for field_name, field_type in quantum_type.fields.items()
        }

    def __str__(self) -> str:
        return str(self.handle)


@dataclass(frozen=True)
class QuantumSymbolList(QuantumVariable):
    handles: list[HandleBinding]

    @staticmethod
    def from_symbols(
        symbols: list[Union[QuantumSymbol, "QuantumSymbolList"]],
    ) -> "QuantumSymbolList":
        handles = list(
            itertools.chain.from_iterable(
                (
                    symbol.handles
                    if isinstance(symbol, QuantumSymbolList)
                    else [symbol.handle]
                )
                for symbol in symbols
            )
        )
        if len(handles) == 0:
            raise ClassiqExpansionError("Empty concatenation expression")
        length: Optional[Expression]
        if any(not symbol.quantum_type.has_size_in_bits for symbol in symbols):
            length = None
        else:
            length = Expression(
                expr=str(sum(symbol.quantum_type.size_in_bits for symbol in symbols))
            )
        for symbol in symbols:
            if isinstance(symbol.quantum_type, QuantumNumeric):
                symbol.quantum_type.reset_bounds()
        return QuantumSymbolList(
            handles=handles, quantum_type=QuantumBitvector(length=length)
        )

    def emit(self) -> HandlesList:
        return HandlesList(handles=self.handles)

    def __str__(self) -> str:
        return str(self.handles)


@dataclass(frozen=True)
class ClassicalSymbol:
    handle: HandleBinding
    classical_type: ClassicalType


@singledispatch
def evaluated_to_str(value: Any) -> str:
    return str(value)


@evaluated_to_str.register
def _evaluated_to_str_list(value: list) -> str:
    return f"[{', '.join(evaluated_to_str(x) for x in value)}]"


@evaluated_to_str.register
def _evaluated_to_str_struct_literal(value: QmodStructInstance) -> str:
    return f"struct_literal({value.struct_declaration.name}, {', '.join(f'{k}={evaluated_to_str(v)}' for k, v in value.fields.items())})"


def _raise_type_error(val: Any, t: type, location_hint: Optional[str]) -> NoReturn:
    if isinstance(val, sympy.Basic) and len(val.free_symbols) > 0:
        symbolic_vars = sorted(map(str, val.free_symbols))
        suffix = f" {location_hint}" if location_hint is not None else ""
        raise ClassiqExpansionError(
            f"Cannot use execution parameter{s(symbolic_vars)} {readable_list(symbolic_vars, quote=True)} in a compile-time context{suffix}"
        )
    raise ClassiqExpansionError(f"Invalid access to expression {val!r} as {t}")


@dataclass(frozen=True)
class Evaluated:  # FIXME: Merge with EvaluatedExpression if possible
    value: Any
    defining_function: Optional["FunctionClosure"] = None

    def as_type(self, t: type[T], location_hint: Optional[str] = None) -> T:
        if t is int:
            return self._as_int(location_hint)  # type: ignore[return-value]

        if not isinstance(self.value, t):
            _raise_type_error(self.value, t, location_hint)

        return self.value

    def _as_int(self, location_hint: Optional[str]) -> int:
        if not isinstance(self.value, (int, float)):
            _raise_type_error(self.value, int, location_hint)

        return int(self.value)

    def emit(self, param: Optional[AnonPositionalArg] = None) -> ArgValue:
        from classiq.model_expansions.closure import FunctionClosure

        if isinstance(self.value, (QuantumVariable, FunctionClosure)):
            return self.value.emit()
        if (
            isinstance(param, AnonQuantumOperandDeclaration)
            and isinstance(self.value, list)
            and all(isinstance(item, FunctionClosure) for item in self.value)
        ):
            return [item.emit() for item in self.value]

        ret = Expression(expr=evaluated_to_str(self.value))
        ret._evaluated_expr = EvaluatedExpression(value=self.value)
        return ret


if TYPE_CHECKING:
    EvaluatedUserDict = UserDict[str, Evaluated]
else:
    EvaluatedUserDict = UserDict


class Scope(EvaluatedUserDict):
    def __init__(
        self,
        data: Optional[dict[str, Evaluated]] = None,
        /,
        *,
        parent: Optional["Scope"] = None,
    ) -> None:
        super().__init__(data or {})
        self._parent: Optional["Scope"] = parent

    @property
    def parent(self) -> Optional["Scope"]:
        return self._parent

    def __getitem__(self, name: str) -> Evaluated:
        if name in self.data:
            return self.data[name]
        if self._parent is not None:
            return self._parent[name]
        raise ClassiqExpansionError(f"Variable {name!r} is undefined")

    def __contains__(self, item: Any) -> bool:
        return item in self.data or (self._parent is not None and item in self._parent)

    def __iter__(self) -> Iterator[str]:
        if self._parent is None:
            return iter(self.data)
        return iter(itertools.chain(self.data, self._parent))

    def iter_without_top_level(self) -> Iterator[str]:
        if self.parent is None:
            return iter(tuple())
        return iter(itertools.chain(self.data, self.parent.iter_without_top_level()))

    def __or__(self, other: Any) -> "Scope":  # type: ignore[override]
        if not (isinstance(other, Scope) and isinstance(self, Scope)):
            raise ClassiqInternalExpansionError

        if self.parent is None:
            parent = other.parent
        elif other.parent is None:
            parent = self.parent
        else:
            parent = self.parent | other.parent

        return Scope(
            (self.data or {}) | (other.data or {}),
            parent=parent,
        )

    def clone(self) -> "Scope":
        return Scope(self.data, parent=self._parent)
