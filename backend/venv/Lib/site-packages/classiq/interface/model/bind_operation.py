from collections.abc import Mapping, Sequence
from typing import Literal

import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.model.handle_binding import ConcreteHandleBinding, HandleBinding
from classiq.interface.model.quantum_statement import HandleMetadata, QuantumOperation

BIND_INPUT_NAME = "bind_input"
BIND_OUTPUT_NAME = "bind_output"


class BindOperation(QuantumOperation):
    kind: Literal["BindOperation"]

    in_handles: list[ConcreteHandleBinding]
    out_handles: list[ConcreteHandleBinding]

    @property
    def wiring_inputs(self) -> Mapping[str, HandleBinding]:
        return {
            f"{BIND_INPUT_NAME}_{i}": handle for i, handle in enumerate(self.in_handles)
        }

    @property
    def readable_inputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location="on the left-hand side of a bind statement",
            )
            for handle in self.in_handles
        ]

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return {
            f"{BIND_OUTPUT_NAME}_{i}": handle
            for i, handle in enumerate(self.out_handles)
        }

    @property
    def readable_outputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location="on the right-hand side of a bind statement",
            )
            for handle in self.out_handles
        ]

    @pydantic.field_validator("in_handles", "out_handles")
    @classmethod
    def validate_handle(cls, handles: list[HandleBinding]) -> list[HandleBinding]:
        for handle in handles:
            if not handle.is_bindable():
                raise ClassiqValueError(f"Cannot bind '{handle}'")

        return handles
