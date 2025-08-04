import abc
from collections.abc import Mapping
from typing import Optional

import pydantic

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.helpers.pydantic_model_helpers import nameables_to_dict
from classiq.interface.model.handle_binding import (
    ConcreteHandleBinding,
    HandleBinding,
)
from classiq.interface.model.quantum_statement import QuantumOperation
from classiq.interface.model.quantum_type import QuantumType


class QuantumExpressionOperation(QuantumOperation):
    expression: Expression = pydantic.Field()
    _var_handles: list[HandleBinding] = pydantic.PrivateAttr(
        default_factory=list,
    )
    _var_types: dict[str, QuantumType] = pydantic.PrivateAttr(
        default_factory=dict,
    )

    @property
    def var_handles(self) -> list[HandleBinding]:
        return self._var_handles

    def set_var_handles(self, var_handles: list[HandleBinding]) -> None:
        self._var_handles = var_handles

    @property
    def var_types(self) -> dict[str, QuantumType]:
        return self._var_types

    def initialize_var_types(
        self,
        var_types: dict[str, QuantumType],
        machine_precision: int,
    ) -> None:
        assert len(var_types) == len(self.var_handles) or len(self.var_handles) == 0
        self._var_types = var_types

    @property
    def wiring_inouts(self) -> Mapping[str, ConcreteHandleBinding]:
        return nameables_to_dict(self.var_handles)

    @property
    def expressions(self) -> list[Expression]:
        return [self.expression]


class QuantumAssignmentOperation(QuantumExpressionOperation):
    result_var: ConcreteHandleBinding = pydantic.Field(
        description="The variable storing the expression result"
    )
    _result_type: Optional[QuantumType] = pydantic.PrivateAttr(
        default=None,
    )

    @property
    def result_type(self) -> QuantumType:
        assert self._result_type is not None
        return self._result_type

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return {self.result_name(): self.result_var}

    @classmethod
    @abc.abstractmethod
    def result_name(cls) -> str:
        raise NotImplementedError()
