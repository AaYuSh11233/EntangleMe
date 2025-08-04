import abc
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Annotated,
    Any,
    ForwardRef,
    Generic,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
    _GenericAlias,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)

from typing_extensions import ParamSpec, Self, _AnnotatedAlias

from classiq.interface.exceptions import (
    ClassiqInternalError,
    ClassiqNotImplementedError,
    ClassiqValueError,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.quantum.qmod_qarray_proxy import (
    ILLEGAL_SLICE_MSG,
    ILLEGAL_SLICING_STEP_MSG,
)
from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.functions.type_name import Struct, TypeName
from classiq.interface.generator.types.qstruct_declaration import QStructDeclaration
from classiq.interface.helpers.classproperty import classproperty
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
    ArithmeticOperationKind,
)
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
    QuantumType,
)
from classiq.interface.source_reference import SourceReference

from classiq.qmod.cparam import ArrayBase, CInt, CParamScalar
from classiq.qmod.generative import (
    generative_mode_context,
    interpret_expression,
    is_generative_mode,
)
from classiq.qmod.model_state_container import QMODULE, ModelStateContainer
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator
from classiq.qmod.semantics.validation.types_validation import validate_qstruct
from classiq.qmod.symbolic_expr import Symbolic, SymbolicExpr
from classiq.qmod.symbolic_type import SYMBOLIC_TYPES, SymbolicTypes
from classiq.qmod.utilities import (
    get_source_ref,
    unwrap_forward_ref,
    varname,
    version_portable_get_args,
)


@contextmanager
def _no_current_expandable() -> Iterator[None]:
    current_expandable = QCallable.CURRENT_EXPANDABLE
    QCallable.CURRENT_EXPANDABLE = None
    try:
        yield
    finally:
        QCallable.CURRENT_EXPANDABLE = current_expandable


def _infer_variable_name(name: Any, depth: int) -> Any:
    if name is not None:
        return name
    name = varname(depth + 1)
    if name is None:
        raise ClassiqValueError(
            "Could not infer variable name. Please specify the variable name explicitly"
        )
    return name


class QVar(Symbolic):
    CONSTRUCTOR_DEPTH: int = 1

    def __init__(
        self,
        origin: Union[None, str, HandleBinding] = None,
        *,
        expr_str: Optional[str] = None,
        depth: int = 2,
    ) -> None:
        name = _infer_variable_name(origin, self.CONSTRUCTOR_DEPTH)
        super().__init__(str(name), True)
        source_ref = (
            get_source_ref(sys._getframe(depth))
            if isinstance(name, str)
            else name.source_ref
        )
        self._base_handle: HandleBinding = (
            HandleBinding(name=name) if isinstance(name, str) else name
        )
        if isinstance(name, str) and QCallable.CURRENT_EXPANDABLE is not None:
            QCallable.CURRENT_EXPANDABLE.add_local_handle(
                name, self.get_qmod_type(), source_ref
            )
        self._expr_str = expr_str if expr_str is not None else str(name)

    def get_handle_binding(self) -> HandleBinding:
        return self._base_handle

    @abc.abstractmethod
    def get_qmod_type(self) -> ConcreteQuantumType:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def to_qvar(
        cls,
        origin: Union[str, HandleBinding],
        type_hint: Any,
        expr_str: Optional[str],
    ) -> Self:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self._expr_str

    @property
    def size(self) -> Union[CParamScalar, int]:
        if is_generative_mode():
            with generative_mode_context(False):
                return interpret_expression(str(self.size))
        return CParamScalar(f"get_field({self}, 'size')")

    @property
    def type_name(self) -> str:
        return self.get_qmod_type().type_name


class QmodExpressionCreator(Protocol):
    """
    A callable that creates a Qmod expression from the provided QVars.
    """

    def __call__(self, **kwargs: QVar) -> SymbolicExpr: ...


_Q = TypeVar("_Q", bound=QVar)
Output = Annotated[_Q, PortDeclarationDirection.Output]
Input = Annotated[_Q, PortDeclarationDirection.Input]
Const = Annotated[
    _Q, TypeModifier.Const
]  # A constant variable, up to a phase dependent on the computational basis state
Permutable = Annotated[
    _Q, TypeModifier.Permutable
]  # A permutable ("quantum free") variable, up to a phase dependent on the computational basis state


class QScalar(QVar, SymbolicExpr):
    CONSTRUCTOR_DEPTH: int = 2

    def __init__(
        self,
        origin: Union[None, str, HandleBinding] = None,
        *,
        _expr_str: Optional[str] = None,
        depth: int = 2,
    ) -> None:
        origin = _infer_variable_name(origin, self.CONSTRUCTOR_DEPTH)
        QVar.__init__(self, origin, expr_str=_expr_str, depth=depth)
        SymbolicExpr.__init__(self, str(origin), True)

    def _insert_arith_operation(
        self,
        expr: SymbolicTypes,
        kind: ArithmeticOperationKind,
        source_ref: SourceReference,
    ) -> None:
        # Fixme: Arithmetic operations are not yet supported on slices (see CAD-12670)
        if TYPE_CHECKING:
            assert QCallable.CURRENT_EXPANDABLE is not None
        QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
            ArithmeticOperation(
                expression=Expression(expr=str(expr)),
                result_var=self.get_handle_binding(),
                operation_kind=kind,
                source_ref=source_ref,
            )
        )

    def _insert_amplitude_loading(
        self, expr: SymbolicTypes, source_ref: SourceReference
    ) -> None:
        if TYPE_CHECKING:
            assert QCallable.CURRENT_EXPANDABLE is not None
        QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
            AmplitudeLoadingOperation(
                expression=Expression(expr=str(expr)),
                result_var=self.get_handle_binding(),
                source_ref=source_ref,
            )
        )

    def __ior__(self, other: Any) -> Self:
        if not isinstance(other, SYMBOLIC_TYPES):
            raise TypeError(
                f"Invalid argument {other!r} for out-of-place arithmetic operation"
            )

        self._insert_arith_operation(
            other, ArithmeticOperationKind.Assignment, get_source_ref(sys._getframe(1))
        )
        return self

    def __ixor__(self, other: Any) -> Self:
        if not isinstance(other, SYMBOLIC_TYPES):
            raise TypeError(
                f"Invalid argument {other!r} for in-place arithmetic operation"
            )

        self._insert_arith_operation(
            other, ArithmeticOperationKind.InplaceXor, get_source_ref(sys._getframe(1))
        )
        return self

    def __iadd__(self, other: Any) -> Self:
        if not isinstance(other, SYMBOLIC_TYPES):
            raise TypeError(
                f"Invalid argument {other!r} for in-place arithmetic operation"
            )

        self._insert_arith_operation(
            other, ArithmeticOperationKind.InplaceAdd, get_source_ref(sys._getframe(1))
        )
        return self

    def __imul__(self, other: Any) -> Self:
        if not isinstance(other, SYMBOLIC_TYPES):
            raise TypeError(
                f"Invalid argument {other!r} for out of ampltiude encoding operation"
            )

        self._insert_amplitude_loading(other, get_source_ref(sys._getframe(1)))
        return self


class QBit(QScalar):
    @classmethod
    def to_qvar(
        cls,
        origin: Union[str, HandleBinding],
        type_hint: Any,
        expr_str: Optional[str],
    ) -> "QBit":
        return QBit(origin, _expr_str=expr_str)

    def get_qmod_type(self) -> ConcreteQuantumType:
        return QuantumBit()


_P = ParamSpec("_P")


class QNum(Generic[_P], QScalar):
    CONSTRUCTOR_DEPTH: int = 3

    def __init__(
        self,
        name: Union[None, str, HandleBinding] = None,
        size: Union[int, CInt, Expression, SymbolicExpr, None] = None,
        is_signed: Union[bool, Expression, SymbolicExpr, None] = None,
        fraction_digits: Union[int, CInt, Expression, None] = None,
        _expr_str: Optional[str] = None,
    ):
        if size is None and (is_signed is not None or fraction_digits is not None):
            raise ClassiqValueError(
                "Cannot assign 'is_signed' and 'fraction_digits' without 'size'"
            )
        if is_signed is not None and fraction_digits is None:
            raise ClassiqValueError(
                "Cannot assign 'is_signed' without 'fraction_digits'"
            )
        if is_signed is None and fraction_digits is not None:
            raise ClassiqValueError(
                "Cannot assign 'fraction_digits' without 'is_signed'"
            )
        self._size = (
            size
            if size is None or isinstance(size, Expression)
            else Expression(expr=str(size))
        )
        self._is_signed = (
            is_signed
            if is_signed is None or isinstance(is_signed, Expression)
            else Expression(expr=str(is_signed))
        )
        self._fraction_digits = (
            fraction_digits
            if fraction_digits is None or isinstance(fraction_digits, Expression)
            else Expression(expr=str(fraction_digits))
        )
        super().__init__(name, _expr_str=_expr_str, depth=3)

    @classmethod
    def to_qvar(
        cls,
        origin: Union[str, HandleBinding],
        type_hint: Any,
        expr_str: Optional[str],
    ) -> "QNum":
        return QNum(origin, *_get_qnum_attributes(type_hint), _expr_str=expr_str)

    def get_qmod_type(self) -> ConcreteQuantumType:
        return QuantumNumeric(
            size=self._size,
            is_signed=self._is_signed,
            fraction_digits=self._fraction_digits,
        )

    @property
    def fraction_digits(self) -> Union[CParamScalar, int]:
        if is_generative_mode():
            with generative_mode_context(False):
                return interpret_expression(str(self.fraction_digits))
        return CParamScalar(f"get_field({self}, 'fraction_digits')")

    @property
    def is_signed(self) -> Union[CParamScalar, bool]:
        if is_generative_mode():
            with generative_mode_context(False):
                return interpret_expression(str(self.is_signed))
        return CParamScalar(f"get_field({self}, 'is_signed')")

    def get_maximal_bounds(self) -> tuple[float, float]:
        if not is_generative_mode():
            raise ClassiqNotImplementedError(
                "get_maximal_bounds() is supported in generative mode only"
            )

        if TYPE_CHECKING:
            assert isinstance(self.size, int)
            assert isinstance(self.is_signed, bool)
            assert isinstance(self.fraction_digits, int)

        return RegisterArithmeticInfo.get_maximal_bounds(
            size=self.size,
            is_signed=self.is_signed,
            fraction_places=self.fraction_digits,
        )

    # Support comma-separated generic args in older Python versions
    if sys.version_info[0:2] < (3, 10):

        def __class_getitem__(cls, args) -> _GenericAlias:
            return _GenericAlias(cls, args)


class QArray(ArrayBase[_P], QVar, NonSymbolicExpr):
    CONSTRUCTOR_DEPTH: int = 3

    # TODO [CAD-18620]: improve type hints
    def __init__(
        self,
        name: Union[None, str, HandleBinding] = None,
        element_type: Union[_GenericAlias, QuantumType] = QBit,
        length: Optional[Union[int, SymbolicExpr, Expression]] = None,
        _expr_str: Optional[str] = None,
    ) -> None:
        self._element_type = element_type
        self._length = (
            length
            if length is None or isinstance(length, Expression)
            else Expression(expr=str(length))
        )
        super().__init__(name, expr_str=_expr_str)

    def __getitem__(self, key: Union[slice, int, SymbolicExpr]) -> Any:
        return (
            self._get_slice(key) if isinstance(key, slice) else self._get_subscript(key)
        )

    def __setitem__(self, *args: Any) -> None:
        pass

    def _get_subscript(self, index: Union[slice, int, SymbolicExpr]) -> Any:
        if isinstance(index, SymbolicExpr) and index.is_quantum:
            raise ClassiqValueError("Non-classical parameter for slicing")

        return _create_qvar_for_qtype(
            self.get_qmod_type().element_type,
            SubscriptHandleBinding(
                base_handle=self._base_handle,
                index=Expression(expr=str(index)),
            ),
            expr_str=f"{self}[{index}]",
        )

    def _get_slice(self, slice_: slice) -> Any:
        if slice_.step is not None:
            raise ClassiqValueError(ILLEGAL_SLICING_STEP_MSG)
        if not isinstance(slice_.start, (int, SymbolicExpr)) or not isinstance(
            slice_.stop, (int, SymbolicExpr)
        ):
            raise ClassiqValueError(ILLEGAL_SLICE_MSG)

        return QArray(
            name=SlicedHandleBinding(
                base_handle=self._base_handle,
                start=Expression(expr=str(slice_.start)),
                end=Expression(expr=str(slice_.stop)),
            ),
            element_type=self._element_type,
            length=slice_.stop - slice_.start,
            _expr_str=f"{self}[{slice_.start}:{slice_.stop}]",
        )

    def __len__(self) -> int:
        raise ClassiqValueError(
            "len(<var>) is not supported for quantum variables - use <var>.len instead"
        )

    if TYPE_CHECKING:

        @property
        def len(self) -> int: ...

    else:

        @property
        def len(self) -> Union[CParamScalar, int]:
            if is_generative_mode():
                with generative_mode_context(False):
                    return interpret_expression(str(self.len))
            return CParamScalar(f"get_field({self}, 'len')")

    @classmethod
    def to_qvar(
        cls,
        origin: Union[str, HandleBinding],
        type_hint: Any,
        expr_str: Optional[str],
    ) -> "QArray":
        return QArray(origin, *_get_qarray_attributes(type_hint), _expr_str=expr_str)

    def get_qmod_type(self) -> QuantumBitvector:
        return QuantumBitvector(
            element_type=(
                self._element_type
                if isinstance(self._element_type, QuantumType)
                else _to_quantum_type(self._element_type)
            ),
            length=self._length,
        )


class QStruct(QVar):
    CONSTRUCTOR_DEPTH: int = 2

    _struct_name: str
    _fields: Mapping[str, QVar]

    def __init__(
        self,
        origin: Union[None, str, HandleBinding] = None,
        _struct_name: Optional[str] = None,
        _fields: Optional[Mapping[str, QVar]] = None,
        _expr_str: Optional[str] = None,
    ) -> None:
        _register_qstruct(type(self), qmodule=QMODULE)
        name = _infer_variable_name(origin, self.CONSTRUCTOR_DEPTH)
        if _struct_name is None or _fields is None:
            with _no_current_expandable():
                temp_var = QStruct.to_qvar(name, type(self), _expr_str)
                _struct_name = temp_var._struct_name
                _fields = temp_var._fields
        self._struct_name = _struct_name
        self._fields = _fields
        for field_name, var in _fields.items():
            setattr(self, field_name, var)
        super().__init__(name, expr_str=_expr_str)

    def get_qmod_type(self) -> ConcreteQuantumType:
        classical_type = Struct(name=self._struct_name)
        classical_type.set_fields(
            {
                field_name: field_var.get_qmod_type()
                for field_name, field_var in self._fields.items()
            }
        )
        return classical_type

    @classmethod
    def to_qvar(
        cls,
        origin: Union[str, HandleBinding],
        type_hint: Any,
        expr_str: Optional[str],
    ) -> "QStruct":
        field_types = {
            field_name: (_get_root_type(field_type), field_type)
            for field_name, field_type in type_hint.__annotations__.items()
        }
        base_handle = HandleBinding(name=origin) if isinstance(origin, str) else origin
        with _no_current_expandable():
            field_vars = {
                field_name: field_class.to_qvar(
                    FieldHandleBinding(base_handle=base_handle, field=field_name),
                    field_type,
                    f"get_field({expr_str if expr_str is not None else str(origin)}, '{field_name}')",
                )
                for field_name, (field_class, field_type) in field_types.items()
            }
        return QStruct(
            origin,
            _struct_name=type_hint.__name__,
            _fields=field_vars,
            _expr_str=expr_str,
        )

    @classproperty
    def num_qubits(cls) -> int:  # noqa: N805
        """
        The total number of qubits in this quantum struct.
        Raises an error if the struct doesn't have a fixed size.
        """
        qvar = cls.to_qvar(HandleBinding(name="dummy"), type_hint=cls, expr_str=None)
        quantum_type = qvar.get_qmod_type()
        if not quantum_type.has_size_in_bits:
            raise ClassiqValueError(
                f"Could not infer the size of struct {qvar._struct_name!r}"
            )
        return quantum_type.size_in_bits


def create_qvar_from_quantum_type(quantum_type: ConcreteQuantumType, name: str) -> QVar:
    return _create_qvar_for_qtype(quantum_type, HandleBinding(name=name))


def _create_qvar_for_qtype(
    qtype: QuantumType, origin: HandleBinding, expr_str: Optional[str] = None
) -> QVar:
    # prevent addition to local handles, since this is used for ports
    with _no_current_expandable():
        if isinstance(qtype, QuantumBit):
            return QBit(origin, _expr_str=expr_str)
        elif isinstance(qtype, QuantumNumeric):
            return QNum(
                origin,
                qtype.size,
                qtype.is_signed,
                qtype.fraction_digits,
                _expr_str=expr_str,
            )
        elif isinstance(qtype, TypeName):
            struct_decl = QMODULE.qstruct_decls[qtype.name]
            return QStruct(
                origin,
                struct_decl.name,
                {
                    field_name: _create_qvar_for_qtype(
                        field_type,
                        FieldHandleBinding(base_handle=origin, field=field_name),
                        f"get_field({expr_str if expr_str is not None else str(origin)}, '{field_name}')",
                    )
                    for field_name, field_type in struct_decl.fields.items()
                },
                _expr_str=expr_str,
            )
        if TYPE_CHECKING:
            assert isinstance(qtype, QuantumBitvector)
        return QArray(origin, qtype.element_type, qtype.length, _expr_str=expr_str)


def get_qvar(qtype: QuantumType, origin: HandleBinding) -> "QVar":
    if isinstance(qtype, QuantumBit):
        return QBit(origin)
    elif isinstance(qtype, QuantumBitvector):
        return QArray(origin, qtype.element_type, qtype.length)
    elif isinstance(qtype, QuantumNumeric):
        return QNum(origin, qtype.size, qtype.is_signed, qtype.fraction_digits)
    elif isinstance(qtype, TypeName):
        return QStruct(
            origin,
            qtype.name,
            {
                field_name: get_qvar(
                    field_type, FieldHandleBinding(base_handle=origin, field=field_name)
                )
                for field_name, field_type in qtype.fields.items()
            },
        )
    raise NotImplementedError


def get_port_from_type_hint(
    py_type: Any,
) -> tuple[QuantumType, PortDeclarationDirection, TypeModifier]:
    direction = PortDeclarationDirection.Inout  # default
    modifier = TypeModifier.Mutable  # default

    if isinstance(py_type, _AnnotatedAlias):
        quantum_type = _to_quantum_type(py_type.__origin__)
        for metadata in py_type.__metadata__:
            if isinstance(metadata, PortDeclarationDirection):
                direction = metadata
            elif isinstance(metadata, TypeModifier):
                modifier = metadata
    else:
        quantum_type = _to_quantum_type(py_type)

    return quantum_type, direction, modifier


def _to_quantum_type(py_type: Any) -> QuantumType:
    root_type = _get_root_type(py_type)
    if not issubclass(root_type, QVar):
        raise ClassiqInternalError(f"Invalid quantum type {py_type}")
    if issubclass(root_type, QBit):
        return QuantumBit()
    elif issubclass(root_type, QNum):
        return _get_quantum_numeric(py_type)
    elif issubclass(root_type, QArray):
        return _get_quantum_bit_vector(py_type)
    elif issubclass(root_type, QStruct):
        return _get_quantum_struct(py_type)
    else:
        raise ClassiqInternalError(f"Invalid quantum type {py_type}")


def _get_quantum_numeric(type_hint: type[QNum]) -> QuantumNumeric:
    size, is_signed, fraction_digits = _get_qnum_attributes(type_hint)
    return QuantumNumeric(
        size=(Expression(expr=_get_type_hint_expr(size)) if size is not None else None),
        is_signed=(
            Expression(expr=_get_type_hint_expr(is_signed))
            if is_signed is not None
            else None
        ),
        fraction_digits=(
            Expression(expr=_get_type_hint_expr(fraction_digits))
            if fraction_digits is not None
            else None
        ),
    )


def _get_qnum_attributes(type_hint: type[QNum]) -> tuple[Any, Any, Any]:
    type_args = version_portable_get_args(type_hint)
    if len(type_args) == 0:
        return None, None, None
    if len(type_args) not in (1, 3):
        raise ClassiqValueError(
            "QNum receives three type arguments: QNum[size: int | CInt, "
            "is_signed: bool | CBool, fraction_digits: int | CInt]"
        )
    if len(type_args) == 1:
        return unwrap_forward_ref(type_args[0]), None, None
    return (
        unwrap_forward_ref(type_args[0]),
        unwrap_forward_ref(type_args[1]),
        unwrap_forward_ref(type_args[2]),
    )


def _get_qarray_attributes(type_hint: type[QArray]) -> tuple[Any, Any]:
    type_args = version_portable_get_args(type_hint)
    if len(type_args) == 0:
        return QBit, None
    first_arg = unwrap_forward_ref(type_args[0])
    if len(type_args) == 1:
        if isinstance(first_arg, (str, int)):
            return QBit, first_arg
        return first_arg, None
    if len(type_args) != 2:
        raise ClassiqValueError(
            "QArray receives two type arguments: QArray[element_type: QVar, "
            "length: int | CInt]"
        )
    second_arg = unwrap_forward_ref(type_args[1])
    return cast(tuple[type[QVar], Any], (first_arg, second_arg))


def _get_quantum_bit_vector(type_hint: type[QArray]) -> QuantumBitvector:
    api_element_type, length = _get_qarray_attributes(type_hint)
    element_type = _to_quantum_type(api_element_type)

    length_expr: Expression | None = None
    if length is not None:
        length_expr = Expression(expr=_get_type_hint_expr(length))

    return QuantumBitvector(element_type=element_type, length=length_expr)


def _get_quantum_struct(type_hint: type[QStruct]) -> Struct:
    decl = _register_qstruct(type_hint, qmodule=QMODULE)
    classical_type = Struct(name=type_hint.__name__)
    if decl is not None:
        classical_type.set_fields(
            {
                field_name: field_type.model_copy(deep=True)
                for field_name, field_type in decl.fields.items()
            }
        )
    return classical_type


def _register_qstruct(
    type_hint: type[QStruct], *, qmodule: ModelStateContainer
) -> Optional[QStructDeclaration]:
    struct_name = type_hint.__name__
    if type_hint is QStruct:
        return None
    if struct_name in qmodule.qstruct_decls:
        return qmodule.qstruct_decls[struct_name]

    # temp assignment for recursive qstruct definitions
    qmodule.qstruct_decls[struct_name] = QStructDeclaration(name=struct_name)
    _validate_fields(type_hint)
    struct_decl = QStructDeclaration(
        name=struct_name,
        fields={
            field_name: _to_quantum_type(field_type)
            for field_name, field_type in type_hint.__annotations__.items()
        },
    )
    qmodule.qstruct_decls[struct_name] = struct_decl
    QStructAnnotator().visit(struct_decl)
    validate_qstruct(struct_decl)
    return struct_decl


def _validate_fields(type_hint: type[QStruct]) -> None:
    field_types = {
        field_name: (_get_root_type(field_type), field_type)
        for field_name, field_type in type_hint.__annotations__.items()
    }
    illegal_fields = [
        (field_name, field_type)
        for field_name, (field_class, field_type) in field_types.items()
        if field_class is None
    ]
    if len(illegal_fields) > 0:
        raise ClassiqValueError(
            f"Field {illegal_fields[0][0]!r} of quantum struct "
            f"{type_hint.__name__} has a non-quantum type "
            f"{illegal_fields[0][1].__name__}."
        )


@runtime_checkable
class _ModelConstant(Protocol):
    # Applies to QConstant
    def add_to_model(self) -> None: ...


def _get_type_hint_expr(type_hint: Any) -> str:
    if isinstance(type_hint, ForwardRef):  # expression in string literal
        return str(type_hint.__forward_arg__)
    if get_origin(type_hint) == Literal:  # explicit numeric literal
        return str(get_args(type_hint)[0])
    if isinstance(
        type_hint, _ModelConstant
    ):  # the Protocol is to prevent circular imports
        type_hint.add_to_model()
    return str(type_hint)  # implicit numeric literal


def _get_root_type(py_type: Any) -> type[QVar]:
    non_annotated_type = (
        py_type.__origin__ if isinstance(py_type, _AnnotatedAlias) else py_type
    )
    root_type = get_origin(non_annotated_type) or non_annotated_type
    if not issubclass(root_type, QVar):
        raise ClassiqValueError(f"Invalid quantum type {root_type.__name__!r}")
    return root_type
