import sys
from abc import ABC, abstractmethod
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Any,
    Generic,
    Union,
    _GenericAlias,
)

from typing_extensions import ParamSpec

from classiq.interface.exceptions import ClassiqValueError

from classiq.qmod.symbolic_expr import Symbolic, SymbolicExpr

if TYPE_CHECKING:
    from classiq.qmod.qmod_variable import QNum

    SymbolicSuperclass = SymbolicExpr
else:
    SymbolicSuperclass = Symbolic


class CParam(SymbolicSuperclass):
    def __init__(self, expr: str) -> None:
        super().__init__(expr, is_quantum=False)


class CParamAbstract(ABC, CParam):

    def __new__(cls, *args: Any, **kwargs: Any) -> "CParamAbstract":
        raise ClassiqValueError(
            f"{cls.__name__} is a Qmod type hint for a classical parameter and it cannot be instantiated. "
            f"Use regular Pythonic values as arguments instead. "
            f"Example:\n\n"
            f"def foo(val: {cls.__name__}) -> None: ...\n\n"
            f"foo({_EXAMPLE_VALUES[cls.__name__]})  # Correct\n"
        )

    @abstractmethod
    def __init__(self) -> None:
        pass


class CInt(CParamAbstract):
    pass


class CReal(CParamAbstract):
    pass


class CBool(CParamAbstract):
    pass


_P = ParamSpec("_P")


class ArrayBase(Generic[_P]):
    # Support comma-separated generic args in older Python versions
    if sys.version_info[0:2] < (3, 10):

        def __class_getitem__(cls, args) -> _GenericAlias:
            return _GenericAlias(cls, args)


class CArray(CParamAbstract, ArrayBase[_P]):
    if TYPE_CHECKING:

        @property
        def len(self) -> int: ...

        def __getitem__(self, idx: Union[int, CInt, slice, "QNum"]) -> Any: ...


Array = CArray


class CParamScalar(CParam, SymbolicExpr):
    def __hash__(self) -> int:
        return hash(str(self))


_EXAMPLE_VALUES: dict[str, Any] = {
    CInt.__name__: 1,
    CReal.__name__: 1.0,
    CBool.__name__: True,
    CArray.__name__: [1, 2],
}
