from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic

from classiq.model_expansions.quantum_operations.emitter import (
    Emitter,
    QuantumStatementT,
)

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class CompositeEmitter(Generic[QuantumStatementT], Emitter[QuantumStatementT]):
    def __init__(
        self,
        interpreter: "BaseInterpreter",
        emitters: Sequence[Emitter[QuantumStatementT]],
    ) -> None:
        super().__init__(interpreter)
        self._emitters = emitters

    def emit(self, statement: QuantumStatementT, /) -> bool:
        for emitter in self._emitters:
            if emitter.emit(statement):
                return True
        self.emit_statement(statement)
        return True
