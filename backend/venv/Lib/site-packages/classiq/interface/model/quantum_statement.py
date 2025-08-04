from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional
from uuid import UUID, uuid4

import pydantic
from pydantic import ConfigDict
from typing_extensions import Self

from classiq.interface.ast_node import ASTNode
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.helpers.pydantic_model_helpers import values_with_discriminator
from classiq.interface.model.handle_binding import (
    ConcreteHandleBinding,
    HandleBinding,
)


class QuantumStatement(ASTNode):
    kind: str
    model_config = ConfigDict(extra="forbid")
    uuid: UUID = pydantic.Field(
        description="A unique identifier for this operation", default_factory=uuid4
    )

    def model_copy(
        self,
        *,
        update: Optional[dict[str, Any]] = None,
        deep: bool = False,
        keep_uuid: bool = False,
    ) -> Self:
        if not keep_uuid:
            update = update or dict()
            update.setdefault("uuid", uuid4())
        return super().model_copy(update=update, deep=deep)

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", cls.__name__)

    @property
    def expressions(self) -> list[Expression]:
        return []


@dataclass
class HandleMetadata:
    handle: HandleBinding
    readable_location: Optional[str] = None


class QuantumOperation(QuantumStatement):
    _generative_blocks: dict[str, Callable] = pydantic.PrivateAttr(default_factory=dict)

    @property
    def wiring_inputs(self) -> Mapping[str, HandleBinding]:
        return dict()

    @property
    def inputs(self) -> Sequence[HandleBinding]:
        return list(self.wiring_inputs.values())

    @property
    def wiring_inouts(self) -> Mapping[str, ConcreteHandleBinding]:
        return dict()

    @property
    def inouts(self) -> Sequence[HandleBinding]:
        return list(self.wiring_inouts.values())

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return dict()

    @property
    def outputs(self) -> Sequence[HandleBinding]:
        return list(self.wiring_outputs.values())

    @property
    def readable_inputs(self) -> Sequence[HandleMetadata]:
        return [HandleMetadata(handle=handle) for handle in self.inputs]

    @property
    def readable_inouts(self) -> Sequence[HandleMetadata]:
        return [HandleMetadata(handle=handle) for handle in self.inouts]

    @property
    def readable_outputs(self) -> Sequence[HandleMetadata]:
        return [HandleMetadata(handle=handle) for handle in self.outputs]

    @property
    def handles_with_directions(
        self,
    ) -> Iterable[tuple[HandleBinding, PortDeclarationDirection]]:
        return (
            [(handle, PortDeclarationDirection.Input) for handle in self.inputs]
            + [(handle, PortDeclarationDirection.Output) for handle in self.outputs]
            + [(handle, PortDeclarationDirection.Inout) for handle in self.inouts]
        )

    def set_generative_block(self, block_name: str, py_callable: Callable) -> None:
        self._generative_blocks[block_name] = py_callable

    def remove_generative_block(self, block_name: str) -> None:
        self._generative_blocks.pop(block_name)

    def get_generative_block(self, block_name: str) -> Callable:
        return self._generative_blocks[block_name]

    def has_generative_block(self, block_name: str) -> bool:
        return block_name in self._generative_blocks

    def is_generative(self) -> bool:
        return len(self._generative_blocks) > 0

    def clear_generative_blocks(self) -> None:
        self._generative_blocks.clear()
