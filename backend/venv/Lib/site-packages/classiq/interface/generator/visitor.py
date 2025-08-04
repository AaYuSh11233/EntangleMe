from collections import abc, defaultdict
from collections.abc import Collection, Mapping, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
)

from pydantic import BaseModel

Key = TypeVar("Key")
NodeType = Union[
    str,
    BaseModel,
    int,
    bool,
    tuple["NodeType", ...],
    Mapping[Key, "NodeType"],
    Sequence["NodeType"],
]

ConcreteBaseModel = TypeVar("ConcreteBaseModel", bound=BaseModel)

RetType = Union[list, str, BaseModel, int, bool, dict, tuple, abc.Mapping, abc.Sequence]
Ret = TypeVar("Ret", bound=RetType)


class Visitor:
    def visit(self, node: NodeType) -> Optional[RetType]:
        for cls in type(node).__mro__:
            method = "visit_" + cls.__name__
            if hasattr(self, method):
                visitor = getattr(self, method)
                return visitor(node)
        return self.generic_visit(node)

    def generic_visit(self, node: NodeType) -> Optional[RetType]:
        if isinstance(node, BaseModel):
            return self.visit_BaseModel(node)

        return node

    def visit_list(self, node: list[NodeType]) -> Optional[RetType]:
        for elem in node:
            self.visit(elem)

        return None

    def visit_dict(self, node: dict[Key, NodeType]) -> Optional[RetType]:
        for value in node.values():
            self.visit(value)

        return None

    def visit_tuple(self, node: tuple[NodeType, ...]) -> Optional[tuple[RetType, ...]]:
        for value in node:
            self.visit(value)

        return None

    def visit_BaseModel(self, node: BaseModel) -> Optional[RetType]:
        for _, value in node:
            self.visit(value)

        return None

    def visit_int(self, n: int) -> Optional[RetType]:
        return None

    def visit_bool(self, b: bool) -> Optional[RetType]:
        return None


class Transformer(Visitor):
    if TYPE_CHECKING:

        def visit(self, node: NodeType) -> Any: ...

    def visit_list(self, node: list[NodeType]) -> list[RetType]:
        return [self.visit(elem) for elem in node]

    def visit_dict(self, node: dict[Key, NodeType]) -> dict[Key, RetType]:
        return {key: self.visit(value) for key, value in node.items()}

    def visit_defaultdict(
        self, node: defaultdict[Key, NodeType]
    ) -> defaultdict[Key, RetType]:
        new_default_factory: Callable[[], RetType] | None = None
        if (default_factory := node.default_factory) is not None:
            new_default_factory = partial(
                self._new_default_factory, default_factory=default_factory
            )
        return defaultdict(new_default_factory, self.visit_dict(node))

    def _new_default_factory(self, default_factory: Callable[[], NodeType]) -> RetType:
        return self.visit(default_factory())

    def visit_tuple(self, node: tuple[NodeType, ...]) -> tuple[RetType, ...]:
        return tuple(self.visit(value) for value in node)

    def visit_BaseModel(
        self, node: BaseModel, fields_to_skip: Optional[Collection[str]] = None
    ) -> RetType:
        fields_to_skip = fields_to_skip or set()

        result: dict[str, Any] = dict()
        for name, value in node:
            if name not in fields_to_skip:
                result[name] = self.visit(value)

        return node.model_copy(update=result)

    def visit_int(self, n: int) -> int:
        return n

    def visit_bool(self, b: bool) -> bool:
        return b
