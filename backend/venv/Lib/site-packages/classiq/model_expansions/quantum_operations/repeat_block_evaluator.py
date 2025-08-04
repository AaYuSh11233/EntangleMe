from collections.abc import Sequence
from typing import TYPE_CHECKING

from classiq.interface.generator.expressions.proxies.classical.classical_scalar_proxy import (
    ClassicalScalarProxy,
)
from classiq.interface.generator.functions.classical_type import Integer
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_function_declaration import PositionalArg
from classiq.interface.model.quantum_statement import QuantumOperation
from classiq.interface.model.repeat import Repeat

from classiq import ClassicalParameterDeclaration
from classiq.model_expansions.quantum_operations.block_evaluator import BlockEvaluator
from classiq.model_expansions.scope import Evaluated, Scope


class RepeatBlockEvaluator(BlockEvaluator):
    def get_params(self, op: QuantumOperation) -> Sequence[PositionalArg]:
        if TYPE_CHECKING:
            assert isinstance(op, Repeat)
        return [
            ClassicalParameterDeclaration(name=op.iter_var, classical_type=Integer())
        ]

    def get_scope(self, op: QuantumOperation) -> Scope:
        if TYPE_CHECKING:
            assert isinstance(op, Repeat)
        scope = super().get_scope(op)
        scope[op.iter_var] = Evaluated(
            value=ClassicalScalarProxy(HandleBinding(name=op.iter_var), Integer()),
            defining_function=self._builder.current_function,
        )
        return scope
