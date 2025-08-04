from typing import TYPE_CHECKING, Any, Union

from classiq.interface.exceptions import ClassiqInternalError, ClassiqValueError
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import Struct, TypeName

from classiq.qmod.builtins.structs import BUILTIN_STRUCT_DECLARATIONS
from classiq.qmod.cparam import (  # noqa: F401
    Array,
    ArrayBase,
    CArray,
    CBool,
    CInt,
    CParam,
    CParamScalar,
    CReal,
)
from classiq.qmod.generative import (
    generative_mode_context,
    interpret_expression,
    is_generative_mode,
)
from classiq.qmod.model_state_container import ModelStateContainer
from classiq.qmod.symbolic_expr import Symbolic, SymbolicExpr

if TYPE_CHECKING:

    SymbolicSuperclass = SymbolicExpr
else:
    SymbolicSuperclass = Symbolic


class CParamList(CParam):
    def __init__(
        self,
        expr: str,
        list_type: Union[ClassicalArray, ClassicalTuple],
        qmodule: ModelStateContainer,
    ) -> None:
        super().__init__(expr)
        self._qmodule = qmodule
        self._list_type = list_type

    def __getitem__(self, key: Any) -> CParam:
        param_type: ClassicalType
        if not isinstance(key, slice):
            if isinstance(self._list_type, ClassicalTuple):
                if isinstance(key, int) and 0 <= key < len(
                    self._list_type.element_types
                ):
                    param_type = self._list_type.element_types[key]
                elif len(self._list_type.element_types) == 0:
                    raise ClassiqValueError("Array is empty")
                else:
                    param_type = self._list_type.element_types[0].get_raw_type()
            else:
                param_type = self._list_type.element_type
        else:
            if not isinstance(self._list_type, ClassicalTuple):
                param_type = self._list_type
            else:
                if (
                    (isinstance(key.start, int) or key.start is None)
                    and (isinstance(key.stop, int) or key.stop is None)
                    and (isinstance(key.step, int) or key.step is None)
                ):
                    param_type = ClassicalTuple(
                        element_types=self._list_type.element_types.__getitem__(key)
                    )
                elif len(self._list_type.element_types) == 0:
                    param_type = self._list_type
                else:
                    param_type = self._list_type.element_types[0].get_raw_type()
            start = key.start if key.start is not None else ""
            stop = key.stop if key.stop is not None else ""
            if key.step is not None:
                key = f"{start}:{key.step}:{stop}"
            else:
                key = f"{start}:{stop}"
        return create_param(
            f"({self})[{key}]",
            param_type,
            qmodule=self._qmodule,
        )

    def __len__(self) -> int:
        raise ClassiqValueError(
            "len(<expr>) is not supported for QMod lists - use <expr>.len instead"
        )

    @property
    def len(self) -> CParamScalar:
        if is_generative_mode():
            with generative_mode_context(False):
                return interpret_expression(str(self.len))
        return CParamScalar(f"get_field({self}, 'len')")


class CParamStruct(CParam):
    def __init__(
        self, expr: str, struct_type: Struct, *, qmodule: ModelStateContainer
    ) -> None:
        super().__init__(expr)
        self._qmodule = qmodule
        self._struct_type = struct_type

    def __getattr__(self, field_name: str) -> CParam:
        return CParamStruct.get_field(
            self._qmodule, str(self), self._struct_type.name, field_name
        )

    @staticmethod
    def get_field(
        qmodule: ModelStateContainer,
        variable_name: str,
        struct_name: str,
        field_name: str,
    ) -> CParam:
        struct_decl = BUILTIN_STRUCT_DECLARATIONS.get(
            struct_name, qmodule.type_decls.get(struct_name)
        )
        assert struct_decl is not None
        field_type = struct_decl.variables.get(field_name)
        if field_type is None:
            raise ClassiqValueError(
                f"{struct_name} {variable_name!r} has no field {field_name!r}. "
                f"Available fields: {', '.join(struct_decl.variables.keys())}"
            )

        return create_param(
            f"get_field({variable_name},{field_name!r})",
            field_type.model_copy(deep=True),
            qmodule=qmodule,
        )


def create_param(
    expr_str: str, ctype: ClassicalType, qmodule: ModelStateContainer
) -> CParam:
    if isinstance(ctype, TypeName) and ctype.has_classical_struct_decl:
        decl = ctype.classical_struct_decl
        ctype = Struct(name=ctype.name)
        ctype.set_classical_struct_decl(decl)
    if isinstance(ctype, (ClassicalArray, ClassicalTuple)):
        return CParamList(expr_str, ctype, qmodule=qmodule)
    elif isinstance(ctype, Struct):
        return CParamStruct(expr_str, ctype, qmodule=qmodule)
    else:
        return CParamScalar(expr_str)


def get_qmod_type(ctype: ClassicalType) -> type:
    if isinstance(ctype, Integer):
        return CInt
    elif isinstance(ctype, Real):
        return CReal
    elif isinstance(ctype, Bool):
        return CBool
    elif isinstance(ctype, ClassicalArray):
        if ctype.length is None:
            return CArray[get_qmod_type(ctype.element_type)]  # type: ignore[misc]
        if ctype.has_length and isinstance(ctype.length.value.value, int):
            return CArray[get_qmod_type(ctype.element_type), ctype.length.value.value]  # type: ignore[misc]
        return CArray[get_qmod_type(ctype.element_type), ctype.length.expr]  # type: ignore[misc]
    elif isinstance(ctype, ClassicalTuple):
        raw_type = ctype.get_raw_type()
        if isinstance(raw_type, ClassicalTuple):
            raise ClassiqInternalError("Tuple is empty")
        return get_qmod_type(raw_type)
    elif isinstance(ctype, TypeName):
        type_ = type(ctype.name, (TypeName,), dict())
        if isinstance(ctype, Struct):
            type_.__dataclass_fields__ = []  # type:ignore[attr-defined]
        return type_
    raise NotImplementedError(
        f"{ctype.__class__.__name__!r} has no QMOD SDK equivalent"
    )
