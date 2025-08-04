from collections.abc import Mapping
from typing import TYPE_CHECKING

from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
)

if TYPE_CHECKING:
    from classiq.interface.model.quantum_type import QuantumType


class QmodQStructProxy(NonSymbolicExpr, QmodSizedProxy):
    def __init__(
        self,
        handle: HandleBinding,
        struct_name: str,
        fields: Mapping[str, "QuantumType"],
    ) -> None:
        self._fields = {
            name: type_.get_proxy(FieldHandleBinding(base_handle=handle, field=name))
            for name, type_ in fields.items()
        }
        size = sum(proxy.size for proxy in self._fields.values())
        super().__init__(handle, size)
        self._struct_name = struct_name

    @property
    def type_name(self) -> str:
        return self._struct_name

    @property
    def fields(self) -> Mapping[str, QmodSizedProxy]:
        return {**super().fields, **self._fields}
