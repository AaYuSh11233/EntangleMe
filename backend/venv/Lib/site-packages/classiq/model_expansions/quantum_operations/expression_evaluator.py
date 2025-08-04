from typing import TYPE_CHECKING

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.model.quantum_statement import QuantumOperation

from classiq.model_expansions.quantum_operations.emitter import Emitter

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class ExpressionEvaluator(Emitter[QuantumOperation]):
    def __init__(self, interpreter: "BaseInterpreter", expression_name: str) -> None:
        super().__init__(interpreter)
        self._expression_name = expression_name

    def emit(self, op: QuantumOperation, /) -> bool:
        expression = getattr(op, self._expression_name)
        if not isinstance(expression, Expression) or expression.is_evaluated():
            return False
        evaluated_expression = self._evaluate_expression(
            expression, preserve_bool_ops=True
        )
        for symbol in self._get_symbols_in_expression(evaluated_expression):
            self._capture_handle(symbol.handle, PortDeclarationDirection.Inout)
        for var_name, var_type in self._get_classical_vars_in_expression(
            evaluated_expression
        ):
            self._capture_classical_var(var_name, var_type)
        op = op.model_copy(
            update={self._expression_name: evaluated_expression, "back_ref": op.uuid}
        )
        self._interpreter.add_to_debug_info(op)
        self._interpreter.emit(op)
        return True
