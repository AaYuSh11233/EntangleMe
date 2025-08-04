import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    TypeVar,
    Union,
    overload,
)

import numpy as np

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    subscript_to_str,
)

from classiq.qmod import model_state_container
from classiq.qmod.declaration_inferrer import python_type_to_qmod
from classiq.qmod.qmod_parameter import (
    CArray,
    CParam,
    CParamScalar,
    CReal,
    create_param,
)
from classiq.qmod.symbolic_expr import SymbolicExpr
from classiq.qmod.symbolic_type import SymbolicTypes
from classiq.qmod.utilities import qmod_val_to_expr_str

pi = SymbolicExpr("pi", False)
E = SymbolicExpr("E", False)
I = SymbolicExpr("I", False)  # noqa: E741
GoldenRatio = SymbolicExpr("GoldenRatio", False)
EulerGamma = SymbolicExpr("EulerGamma", False)
Catalan = SymbolicExpr("Catalan", False)


def _unwrap_numpy(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, list):
        return list(map(_unwrap_numpy, x))
    return x


T = TypeVar("T", bound=CParam)


@overload
def symbolic_function(*args: Any, return_type: None = None) -> CParamScalar: ...


@overload
def symbolic_function(*args: Any, return_type: type[T]) -> T: ...


def symbolic_function(*args: Any, return_type: Optional[type[T]] = None) -> CParam:
    qmodule = (
        model_state_container.QMODULE
    )  # FIXME: https://classiq.atlassian.net/browse/CAD-15126
    str_args = [str(_unwrap_numpy(x)) for x in args]
    expr = f"{sys._getframe(1).f_code.co_name}({','.join(str_args)})"

    if return_type is None:
        return CParamScalar(expr)

    if TYPE_CHECKING:
        assert return_type is not None

    qmod_type = python_type_to_qmod(return_type, qmodule=qmodule)
    if qmod_type is None:
        raise ClassiqValueError(
            f"Unsupported return type for symbolic function: {return_type}"
        )

    return create_param(
        expr,
        qmod_type,
        qmodule,
    )


def sin(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def cos(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def tan(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def cot(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def sec(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def csc(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def asin(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def acos(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def atan(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def acot(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def asec(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def acsc(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def sinh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def cosh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def tanh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def coth(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def sech(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def csch(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def asinh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def acosh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def atanh(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def acoth(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def asech(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def exp(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def log(x: SymbolicTypes, base: SymbolicTypes = E) -> CParamScalar:
    return symbolic_function(x, base)


def ln(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def sqrt(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def abs(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def floor(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def ceiling(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def erf(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def erfc(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def gamma(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def beta(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def besselj(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def bessely(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def besseli(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def besselk(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def dirichlet_eta(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def polygamma(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def loggamma(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def factorial(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def binomial(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def subfactorial(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def primorial(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def bell(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def bernoulli(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def euler(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def catalan(x: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x)


def Piecewise(*args: tuple[SymbolicTypes, SymbolicTypes]) -> CParamScalar:  # noqa: N802
    return symbolic_function(*args)


def max(x: SymbolicTypes, y: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x, y)


def min(x: SymbolicTypes, y: SymbolicTypes) -> CParamScalar:
    return symbolic_function(x, y)


def logical_and(x: SymbolicTypes, y: SymbolicTypes) -> SymbolicExpr:
    return SymbolicExpr._binary_op(x, y, "and")


def logical_or(x: SymbolicTypes, y: SymbolicTypes) -> SymbolicExpr:
    return SymbolicExpr._binary_op(x, y, "or")


def logical_not(x: SymbolicTypes) -> SymbolicExpr:
    return SymbolicExpr._unary_op(x, "not")


def mod_inverse(a: SymbolicTypes, m: SymbolicTypes) -> CParamScalar:
    return symbolic_function(a, m)


def sum(arr: SymbolicTypes) -> CParamScalar:
    return symbolic_function(arr)


def subscript(
    array: Union[list, CArray[CReal], np.ndarray],
    index: Any,
) -> CParamScalar:
    return CParamScalar(
        expr=f"{qmod_val_to_expr_str(_unwrap_numpy(array))}[{subscript_to_str(index)}]"
    )


__all__ = [
    "Catalan",
    "E",
    "EulerGamma",
    "GoldenRatio",
    "I",
    "Piecewise",
    "abs",
    "acos",
    "acosh",
    "acot",
    "acoth",
    "acsc",
    "asec",
    "asech",
    "asin",
    "asinh",
    "atan",
    "atanh",
    "bell",
    "bernoulli",
    "besseli",
    "besselj",
    "besselk",
    "bessely",
    "beta",
    "binomial",
    "catalan",
    "ceiling",
    "cos",
    "cosh",
    "cot",
    "coth",
    "csc",
    "csch",
    "dirichlet_eta",
    "erf",
    "erfc",
    "euler",
    "exp",
    "factorial",
    "floor",
    "gamma",
    "ln",
    "log",
    "loggamma",
    "logical_and",
    "logical_not",
    "logical_or",
    "max",
    "min",
    "mod_inverse",
    "pi",
    "polygamma",
    "primorial",
    "sec",
    "sech",
    "sin",
    "sinh",
    "sqrt",
    "subfactorial",
    "subscript",
    "sum",
    "tan",
    "tanh",
]


def __dir__() -> list[str]:
    return __all__
