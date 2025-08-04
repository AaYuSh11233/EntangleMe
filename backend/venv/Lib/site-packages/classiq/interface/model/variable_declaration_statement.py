from typing import Any, Literal, Optional

import pydantic

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.concrete_types import (
    ConcreteQuantumType,
    ConcreteType,
)
from classiq.interface.model.quantum_statement import QuantumStatement
from classiq.interface.model.quantum_type import QuantumType


class VariableDeclarationStatement(QuantumStatement):
    kind: Literal["VariableDeclarationStatement"]

    name: str
    quantum_type: Optional[ConcreteQuantumType] = None
    qmod_type: ConcreteType

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_qmod_type(cls, values: Any) -> dict[str, Any]:
        if isinstance(values, dict):
            if "quantum_type" in values and (
                "qmod_type" not in values or values["qmod_type"] is None
            ):
                values["qmod_type"] = values["quantum_type"]
                values["quantum_type"] = None
            return values
        if values.quantum_type is not None and values.qmod_type is None:
            values.qmod_type = values.quantum_type
            values.quantum_type = None
        return values

    @property
    def expressions(self) -> list[Expression]:
        return self.qmod_type.expressions

    @property
    def is_quantum(self) -> bool:
        return isinstance(self.qmod_type, QuantumType)
