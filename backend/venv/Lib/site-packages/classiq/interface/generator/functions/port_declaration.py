from typing import Any

from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.function_params import PortDirection


class PortDeclarationDirection(StrEnum):
    Input = "input"
    Inout = "inout"
    Output = "output"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PortDeclarationDirection):
            return super().__eq__(other)
        if isinstance(other, PortDirection):
            return self == self.Inout or self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def includes_port_direction(self, direction: PortDirection) -> bool:
        return self in (direction, self.Inout)

    @property
    def is_input(self) -> bool:
        return self.includes_port_direction(PortDirection.Input)

    @property
    def is_output(self) -> bool:
        return self.includes_port_direction(PortDirection.Output)

    @classmethod
    def from_port_direction(
        cls, port_direction: PortDirection
    ) -> "PortDeclarationDirection":
        return cls(port_direction.value)
