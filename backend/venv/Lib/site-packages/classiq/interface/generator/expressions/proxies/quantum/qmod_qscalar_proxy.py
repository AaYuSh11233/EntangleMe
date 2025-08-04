from collections.abc import Mapping
from typing import Any, Optional, Union

import sympy
from sympy import Symbol
from typing_extensions import Self

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.model.handle_binding import HandleBinding


class QmodQScalarProxy(Symbol, QmodSizedProxy):
    def __new__(cls, handle: HandleBinding, **assumptions: bool) -> "QmodQScalarProxy":
        return super().__new__(cls, handle.qmod_expr, **assumptions)

    def __init__(self, handle: HandleBinding, size: int) -> None:
        super().__init__(handle, size)

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: Optional[dict]) -> Self:
        return self


class QmodQBitProxy(QmodQScalarProxy):
    def __init__(self, handle: HandleBinding) -> None:
        super().__init__(handle, 1)

    @property
    def type_name(self) -> str:
        return "Quantum bit"


class QmodQNumProxy(QmodQScalarProxy):
    def __init__(
        self,
        handle: HandleBinding,
        size: Union[int, sympy.Basic],
        fraction_digits: Union[int, sympy.Basic],
        is_signed: Union[bool, sympy.Basic],
    ) -> None:
        super().__init__(handle, size)
        if (
            isinstance(fraction_digits, int)
            and isinstance(size, int)
            and fraction_digits > size
        ):
            raise ClassiqValueError(
                f"Quantum numeric of size {size} cannot have {fraction_digits} "
                f"fraction digits"
            )
        self._fraction_digits = fraction_digits
        self._is_signed = is_signed

    @property
    def type_name(self) -> str:
        return "Quantum numeric"

    @property
    def fraction_digits(self) -> Union[int, sympy.Basic]:
        return self._fraction_digits

    @property
    def is_signed(self) -> Union[bool, sympy.Basic]:
        return self._is_signed

    @property
    def fields(self) -> Mapping[str, Any]:
        return {
            **super().fields,
            "is_signed": self.is_signed,
            "fraction_digits": self.fraction_digits,
        }
