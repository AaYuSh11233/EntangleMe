from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Union

import sympy

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.model.handle_binding import (
    HandleBinding,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)

if TYPE_CHECKING:
    from classiq.interface.model.quantum_type import QuantumType


ILLEGAL_SLICING_STEP_MSG = "Slicing with a step of a quantum variable is not supported"
ILLEGAL_SLICE_MSG = "Quantum array slice must be of the form [<int-value>:<int-value>]."


class QmodQArrayProxy(NonSymbolicExpr, QmodSizedProxy):
    def __init__(
        self,
        handle: HandleBinding,
        element_type: "QuantumType",
        element_size: Union[int, sympy.Basic],
        length: Union[int, sympy.Basic],
    ) -> None:
        super().__init__(handle, element_size * length)
        self._length = length
        self._element_type = element_type
        self._element_size = element_size

    def __getitem__(self, key: Any) -> "QmodSizedProxy":
        return (
            self._get_slice(key) if isinstance(key, slice) else self._get_subscript(key)
        )

    def _get_subscript(self, index: Any) -> "QmodSizedProxy":
        return self._element_type.get_proxy(
            SubscriptHandleBinding(
                base_handle=self.handle,
                index=Expression(expr=str(index)),
            )
        )

    def _get_slice(self, slice_: slice) -> "QmodSizedProxy":
        if slice_.step is not None:
            raise ClassiqValueError(ILLEGAL_SLICING_STEP_MSG)
        return QmodQArrayProxy(
            SlicedHandleBinding(
                base_handle=self.handle,
                start=Expression(expr=str(slice_.start)),
                end=Expression(expr=str(slice_.stop)),
            ),
            self._element_type,
            self._element_size,
            slice_.stop - slice_.start,
        )

    @property
    def type_name(self) -> str:
        return "Quantum array"

    @property
    def len(self) -> Union[int, sympy.Basic]:
        return self._length

    @property
    def fields(self) -> Mapping[str, Any]:
        return {**super().fields, "len": self.len}

    @property
    def size(self) -> int:
        return self.len * self._element_size
