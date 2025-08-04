from typing import Literal

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumExpressionOperation,
)


class PhaseOperation(QuantumExpressionOperation):
    kind: Literal["PhaseOperation"]
    theta: Expression

    @property
    def expressions(self) -> list[Expression]:
        return super().expressions + [self.theta]
