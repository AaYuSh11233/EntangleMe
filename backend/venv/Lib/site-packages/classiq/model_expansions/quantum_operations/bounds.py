from typing import TYPE_CHECKING

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.model.bounds import SetBoundsStatement

from classiq.model_expansions.quantum_operations.bind import Emitter
from classiq.model_expansions.scope import QuantumSymbol
from classiq.qmod.qmod_variable import QuantumNumeric

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class SetBoundsEmitter(Emitter[SetBoundsStatement]):
    def __init__(
        self, interpreter: "BaseInterpreter", keep_statement: bool = True
    ) -> None:
        super().__init__(interpreter)
        self._keep_statement = keep_statement

    def emit(self, op: SetBoundsStatement, /) -> bool:
        target = self._interpreter.evaluate(op.target).as_type(QuantumSymbol)
        if not isinstance(target.quantum_type, QuantumNumeric):
            raise ClassiqExpansionError(
                f"Cannot set bounds of a non-numeric variable {op.target.qmod_expr!r}"
            )

        if op.lower_bound is not None and op.upper_bound is not None:
            target.quantum_type.set_bounds(
                (op.lower_bound.to_float_value(), op.upper_bound.to_float_value())
            )
        else:
            target.quantum_type.reset_bounds()
        if self._keep_statement:
            self.emit_statement(op)
        return True
