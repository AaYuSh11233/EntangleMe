from collections.abc import Sequence
from itertools import chain
from typing import TYPE_CHECKING, Any, Union

import pydantic
from pydantic import ConfigDict, Field
from typing_extensions import Self

from classiq.interface.ast_node import ASTNode
from classiq.interface.generator.expressions.expression import Expression

HANDLE_ID_SEPARATOR = "___"


def _get_expr_id(expr: Expression) -> str:
    if expr.expr.isidentifier() or expr.expr.isnumeric():
        return expr.expr
    return str(abs(hash(expr.expr)))


class HandleBinding(ASTNode):
    name: str = Field(default=None)
    model_config = ConfigDict(frozen=True, extra="forbid")

    def __str__(self) -> str:
        return self.name

    @property
    def qmod_expr(self) -> str:
        return self.name

    def is_bindable(self) -> bool:
        return True

    @property
    def identifier(self) -> str:
        return self.name

    def collapse(self) -> "HandleBinding":
        return self

    def prefixes(self) -> Sequence["HandleBinding"]:
        """
        Split the handle into prefixes:
        a.b[0].c --> [a, a.b, a.b[0], a.b[0].c]
        """
        return [self]

    def _tail_overlaps(self, other_handle: "HandleBinding") -> bool:
        return self.name == other_handle.name

    def overlaps(self, other_handle: "HandleBinding") -> bool:
        self_prefixes = self.collapse().prefixes()
        other_prefixes = other_handle.collapse().prefixes()
        return all(
            self_prefix._tail_overlaps(other_prefix)
            for self_prefix, other_prefix in zip(self_prefixes, other_prefixes)
        )

    def rename(self, name: str) -> Self:
        return self.model_copy(update=dict(name=name))

    def replace_prefix(
        self, prefix: "HandleBinding", replacement: "HandleBinding"
    ) -> "HandleBinding":
        if self == prefix:
            return replacement
        return self

    def __contains__(self, other_handle: "HandleBinding") -> bool:
        return self.collapse() in other_handle.collapse().prefixes()

    def is_constant(self) -> bool:
        return True

    def expressions(self) -> list[Expression]:
        return []


class NestedHandleBinding(HandleBinding):
    base_handle: "ConcreteHandleBinding"

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_name(cls, values: Any) -> dict[str, Any]:
        if isinstance(values, dict):
            orig = values
            while "base_handle" in dict(values):
                values = dict(values)["base_handle"]
            orig["name"] = dict(values).get("name")
            return orig
        if isinstance(values, NestedHandleBinding):
            values.name = values.base_handle.name
            return values.model_dump()
        return values

    def is_bindable(self) -> bool:
        return False

    def prefixes(self) -> Sequence["HandleBinding"]:
        return list(chain.from_iterable([self.base_handle.prefixes(), [self]]))

    def rename(self, name: str) -> Self:
        return self.model_copy(
            update=dict(name=name, base_handle=self.base_handle.rename(name))
        )

    def replace_prefix(
        self, prefix: HandleBinding, replacement: HandleBinding
    ) -> HandleBinding:
        if self == prefix:
            return replacement
        new_base_handle = self.base_handle.replace_prefix(prefix, replacement)
        if new_base_handle is not self.base_handle:
            return self.model_copy(
                update=dict(name=new_base_handle.name, base_handle=new_base_handle)
            )
        return self

    def is_constant(self) -> bool:
        return self.base_handle.is_constant()

    def expressions(self) -> list[Expression]:
        return self.base_handle.expressions()


class SubscriptHandleBinding(NestedHandleBinding):
    index: Expression
    model_config = ConfigDict(frozen=True, extra="forbid")

    def __str__(self) -> str:
        return f"{self.base_handle}[{self.index}]"

    @property
    def qmod_expr(self) -> str:
        return f"{self.base_handle.qmod_expr}[{self.index}]"

    @property
    def identifier(self) -> str:
        return (
            f"{self.base_handle.identifier}{HANDLE_ID_SEPARATOR}"
            f"{_get_expr_id(self.index)}"
        )

    def collapse(self) -> HandleBinding:
        if isinstance(self.base_handle, SlicedHandleBinding):
            return SubscriptHandleBinding(
                base_handle=self.base_handle.base_handle,
                index=self._get_collapsed_index(),
            ).collapse()
        return SubscriptHandleBinding(
            base_handle=self.base_handle.collapse(),
            index=self.index,
        )

    def _get_collapsed_index(self) -> Expression:
        if TYPE_CHECKING:
            assert isinstance(self.base_handle, SlicedHandleBinding)
        if (
            self.index.is_evaluated()
            and self.index.is_constant()
            and self.base_handle.start.is_evaluated()
            and self.base_handle.start.is_constant()
        ):
            return Expression(
                expr=str(
                    self.base_handle.start.to_int_value() + self.index.to_int_value()
                )
            )
        return Expression(expr=f"({self.base_handle.start})+({self.index})")

    def _tail_overlaps(self, other_handle: "HandleBinding") -> bool:
        if isinstance(other_handle, SubscriptHandleBinding):
            return self.index == other_handle.index
        if (
            isinstance(other_handle, SlicedHandleBinding)
            and self.index.is_evaluated()
            and self.index.is_constant()
            and other_handle.is_constant()
        ):
            return (
                other_handle.start.to_int_value()
                <= self.index.to_int_value()
                < other_handle.end.to_int_value()
            )
        return False

    def replace_prefix(
        self, prefix: HandleBinding, replacement: HandleBinding
    ) -> HandleBinding:
        if (
            isinstance(prefix, SlicedHandleBinding)
            and self.base_handle == prefix.base_handle
            and self.index.is_evaluated()
            and self.index.is_constant()
            and prefix.is_constant()
            and prefix.start.to_int_value()
            <= self.index.to_int_value()
            < prefix.end.to_int_value()
        ):
            return SubscriptHandleBinding(
                base_handle=replacement,
                index=Expression(
                    expr=str(self.index.to_int_value() - prefix.start.to_int_value())
                ),
            )
        return super().replace_prefix(prefix, replacement)

    def is_constant(self) -> bool:
        return (
            super().is_constant()
            and self.index.is_evaluated()
            and self.index.is_constant()
        )

    def expressions(self) -> list[Expression]:
        return super().expressions() + [self.index]


class SlicedHandleBinding(NestedHandleBinding):
    start: Expression
    end: Expression
    model_config = ConfigDict(frozen=True, extra="forbid")

    def __str__(self) -> str:
        return f"{self.base_handle}[{self.start}:{self.end}]"

    @property
    def qmod_expr(self) -> str:
        return f"{self.base_handle.qmod_expr}[{self.start}:{self.end}]"

    @property
    def identifier(self) -> str:
        return (
            f"{self.base_handle.identifier}{HANDLE_ID_SEPARATOR}"
            f"{_get_expr_id(self.start)}_{_get_expr_id(self.end)}"
        )

    def collapse(self) -> HandleBinding:
        if isinstance(self.base_handle, SlicedHandleBinding):
            return SlicedHandleBinding(
                base_handle=self.base_handle.base_handle,
                start=self._get_collapsed_start(),
                end=self._get_collapsed_stop(),
            ).collapse()
        return SlicedHandleBinding(
            base_handle=self.base_handle.collapse(),
            start=self.start,
            end=self.end,
        )

    def _tail_overlaps(self, other_handle: "HandleBinding") -> bool:
        if not self.is_constant():
            return False
        start = self.start.to_int_value()
        end = self.end.to_int_value()
        if (
            isinstance(other_handle, SubscriptHandleBinding)
            and other_handle.index.is_evaluated()
            and other_handle.index.is_constant()
        ):
            return start <= other_handle.index.to_int_value() < end
        if isinstance(other_handle, SlicedHandleBinding) and other_handle.is_constant():
            other_start = other_handle.start.to_int_value()
            other_end = other_handle.end.to_int_value()
            return start <= other_start < end or other_start <= start < other_end
        return False

    def _get_collapsed_start(self) -> Expression:
        if TYPE_CHECKING:
            assert isinstance(self.base_handle, SlicedHandleBinding)
        if (
            self.start.is_evaluated()
            and self.start.is_constant()
            and self.base_handle.start.is_evaluated()
            and self.base_handle.start.is_constant()
        ):
            return Expression(
                expr=str(
                    self.base_handle.start.to_int_value() + self.start.to_int_value()
                )
            )
        return Expression(expr=f"({self.base_handle.start})+({self.start})")

    def _get_collapsed_stop(self) -> Expression:
        if TYPE_CHECKING:
            assert isinstance(self.base_handle, SlicedHandleBinding)
        if (
            self.is_constant()
            and self.base_handle.start.is_evaluated()
            and self.base_handle.start.is_constant()
        ):
            return Expression(
                expr=str(
                    self.end.to_int_value()
                    - self.start.to_int_value()
                    + self.base_handle.start.to_int_value()
                )
            )
        return Expression(
            expr=f"({self.end})-({self.start})+({self.base_handle.start})"
        )

    def replace_prefix(
        self, prefix: HandleBinding, replacement: HandleBinding
    ) -> HandleBinding:
        if self == prefix:
            return replacement
        if (
            isinstance(prefix, SlicedHandleBinding)
            and self.base_handle == prefix.base_handle
            and self.is_constant()
            and prefix.is_constant()
        ):
            prefix_start = prefix.start.to_int_value()
            prefix_end = prefix.end.to_int_value()
            self_start = self.start.to_int_value()
            self_end = self.end.to_int_value()
            if (
                prefix_start <= self_start < prefix_end
                and prefix_start < self_end <= prefix_end
            ):
                return SlicedHandleBinding(
                    base_handle=replacement,
                    start=Expression(expr=str(self_start - prefix_start)),
                    end=Expression(expr=str(self_end - prefix_start)),
                )
        return super().replace_prefix(prefix, replacement)

    def is_constant(self) -> bool:
        return (
            super().is_constant()
            and self.start.is_evaluated()
            and self.start.is_constant()
            and self.end.is_evaluated()
            and self.end.is_constant()
        )

    def expressions(self) -> list[Expression]:
        return super().expressions() + [self.start, self.end]


class FieldHandleBinding(NestedHandleBinding):
    field: str
    model_config = ConfigDict(frozen=True, extra="forbid")

    def __str__(self) -> str:
        return f"{self.base_handle}.{self.field}"

    @property
    def qmod_expr(self) -> str:
        return f"get_field({self.base_handle.qmod_expr}, '{self.field}')"

    @property
    def identifier(self) -> str:
        return f"{self.base_handle.identifier}{HANDLE_ID_SEPARATOR}{self.field}"

    def collapse(self) -> HandleBinding:
        return FieldHandleBinding(
            base_handle=self.base_handle.collapse(),
            field=self.field,
        )

    def _tail_overlaps(self, other_handle: "HandleBinding") -> bool:
        return (
            isinstance(other_handle, FieldHandleBinding)
            and self.field == other_handle.field
        )


ConcreteHandleBinding = Union[
    HandleBinding,
    SubscriptHandleBinding,
    SlicedHandleBinding,
    FieldHandleBinding,
]
SubscriptHandleBinding.model_rebuild()
SlicedHandleBinding.model_rebuild()
FieldHandleBinding.model_rebuild()


class HandlesList(ASTNode):
    handles: list["GeneralHandle"]


GeneralHandle = Union[ConcreteHandleBinding, HandlesList]
HandlesList.model_rebuild()
