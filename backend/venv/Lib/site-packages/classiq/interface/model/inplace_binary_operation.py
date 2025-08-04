from collections.abc import Mapping, Sequence
from typing import Literal, Union

from classiq.interface.enum_utils import StrEnum
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.handle_binding import ConcreteHandleBinding, HandleBinding
from classiq.interface.model.quantum_statement import HandleMetadata, QuantumOperation


class BinaryOperation(StrEnum):
    Addition = "inplace_add"
    Xor = "inplace_xor"


class InplaceBinaryOperation(QuantumOperation):
    kind: Literal["InplaceBinaryOperation"]

    target: ConcreteHandleBinding
    value: Union[ConcreteHandleBinding, Expression]
    operation: BinaryOperation

    @property
    def wiring_inouts(self) -> Mapping[str, HandleBinding]:
        inouts = {self.target.name: self.target}
        if isinstance(self.value, HandleBinding):
            inouts[self.value.name] = self.value
        return inouts

    @property
    def readable_inouts(self) -> Sequence[HandleMetadata]:
        suffix = f" of an in-place {self.operation.name.lower()} statement"
        readable_inouts = [
            HandleMetadata(
                handle=self.target, readable_location=f"as the target{suffix}"
            )
        ]
        if isinstance(self.value, HandleBinding):
            readable_inouts.append(
                HandleMetadata(
                    handle=self.value, readable_location=f"as the value{suffix}"
                )
            )
        return readable_inouts

    @property
    def expressions(self) -> list[Expression]:
        return [self.value] if isinstance(self.value, Expression) else []
