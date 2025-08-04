import dataclasses
import inspect
import itertools
import keyword
import sys
from collections import Counter
from collections.abc import Iterable
from enum import Enum as PythonEnum
from types import FrameType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ForwardRef,
    Literal,
    Optional,
    Union,
    get_args,
    get_origin,
    overload,
)

import sympy
from typing_extensions import ParamSpec

from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.source_reference import SourceReference

if TYPE_CHECKING:
    from classiq.qmod.qmod_variable import QVar


def mangle_keyword(name: str) -> str:
    if keyword.iskeyword(name):
        name = f"{name}_"
    return name


@overload
def unmangle_keyword(name: str) -> str:
    pass


@overload
def unmangle_keyword(name: None) -> None:
    pass


def unmangle_keyword(name: Optional[str]) -> Optional[str]:
    if name is None:
        return None
    if name[-1] == "_" and keyword.iskeyword(name[:-1]):
        name = name[:-1]
    return name


def version_portable_get_args(py_type: type) -> tuple:
    if get_origin(py_type) is None:
        return tuple()
    if sys.version_info[0:2] < (3, 10):
        type_args = get_args(py_type)  # The result of __class_getitem__
    else:
        type_args = get_args(py_type)[0]
    if not isinstance(type_args, tuple):
        return (type_args,)
    return tuple(
        (
            version_portable_get_args(type_arg)[0]
            if get_origin(type_arg) == Literal
            else type_arg
        )
        for type_arg in type_args
    )


def get_source_ref(frame: FrameType) -> SourceReference:
    filename = inspect.getfile(frame)
    lineno = frame.f_lineno
    if sys.version_info[0:2] < (3, 11) or frame.f_lasti < 0:
        source_ref = SourceReference(
            file_name=filename,
            start_line=lineno - 1,
            start_column=-1,
            end_line=-1,
            end_column=-1,
        )
    else:
        positions_gen = frame.f_code.co_positions()
        positions = next(itertools.islice(positions_gen, frame.f_lasti // 2, None))
        source_ref = SourceReference(
            file_name=filename,
            start_line=(positions[0] or 0) - 1,
            start_column=(positions[2] or 0) - 1,
            end_line=(positions[1] or 0) - 1,
            end_column=(positions[3] or 0) - 1,
        )
    return source_ref


def qmod_val_to_expr_str(val: Any) -> str:
    if isinstance(val, sympy.Basic):
        return str(val)

    if dataclasses.is_dataclass(type(val)):
        kwargs_str = ", ".join(
            [
                f"{field.name}={qmod_val_to_expr_str(vars(val)[field.name])}"
                for field in dataclasses.fields(val)
            ]
        )
        return f"struct_literal({type(val).__name__}, {kwargs_str})"

    if isinstance(val, QmodStructInstance):
        kwargs_str = ", ".join(
            [
                f"{field_name}={qmod_val_to_expr_str(field_val)}"
                for field_name, field_val in val.fields.items()
            ]
        )
        return f"struct_literal({val.struct_declaration.name}, {kwargs_str})"

    if isinstance(val, Iterable):
        elements_str = ", ".join([qmod_val_to_expr_str(elem) for elem in val])
        return f"[{elements_str}]"

    if isinstance(val, PythonEnum):
        return f"{type(val).__name__}.{val.name}"

    return str(val)


def unwrap_forward_ref(x: Any) -> Any:
    if isinstance(x, ForwardRef):
        return x.__forward_arg__
    return x


def varname(depth: int) -> Optional[str]:
    frame = sys._getframe(depth)
    codes = inspect.getframeinfo(frame).code_context
    if codes is None or len(codes) != 1:
        return None
    code = codes[0]
    if "=" not in code:
        return None
    var_name = code.split("=")[0].strip()
    if ":" in var_name:
        var_name = var_name.split(":")[0].strip()
    if not var_name.isidentifier() or keyword.iskeyword(var_name):
        return None
    return var_name


Params = ParamSpec("Params")


def suppress_return_value(func: Callable[Params, None]) -> Callable[Params, None]:
    # An empty decorator suppresses mypy's func-returns-value error when assigning the
    # return value of a None-returning function
    return func


Statements = Union[None, list[Union[None, "QVar"]], tuple[Union[None, "QVar"], ...]]


def _eval_qnum(val: int, size: int, is_signed: bool, fraction_digits: int) -> float:
    if val < 0 or val >= 2**size:
        raise ValueError
    if size == 1 and is_signed and fraction_digits == 1:
        return -0.5 if val == 1 else 0
    if is_signed and val & (1 << (size - 1)) > 0:
        val ^= 1 << (size - 1)
        val -= 1 << (size - 1)
    return val * 2**-fraction_digits


def qnum_values(size: int, is_signed: bool, fraction_digits: int) -> list[float]:
    return [_eval_qnum(i, size, is_signed, fraction_digits) for i in range(2**size)]


def qnum_attributes(max_size: int) -> list[tuple[int, bool, int]]:
    return [(1, True, 1)] + [
        (size, is_signed, fraction_digits)
        for size in range(1, max_size + 1)
        for is_signed in (False, True)
        for fraction_digits in range(size - int(is_signed) + 1)
    ]


_VAR_NAME_COUNTER: Counter[str] = Counter()


def get_temp_var_name(var_name: str = "temp") -> str:
    n = _VAR_NAME_COUNTER[var_name]
    _VAR_NAME_COUNTER[var_name] += 1
    return f"{var_name}_{n}"


RealFunction = Callable[Params, float]
