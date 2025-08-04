from typing import TYPE_CHECKING

import sympy

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.classical_if import ClassicalIf
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_lambda_function import OperandIdentifier
from classiq.interface.model.quantum_statement import QuantumStatement

from classiq.model_expansions.closure import FunctionClosure
from classiq.model_expansions.quantum_operations.call_emitter import CallEmitter
from classiq.model_expansions.quantum_operations.declarative_call_emitter import (
    DeclarativeCallEmitter,
)
from classiq.qmod.semantics.error_manager import ErrorManager

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class QuantumFunctionCallEmitter(CallEmitter[QuantumFunctionCall]):
    def __init__(self, interpreter: "BaseInterpreter") -> None:
        super().__init__(interpreter)
        self._model = self._interpreter._model

    def emit(self, call: QuantumFunctionCall, /) -> bool:
        if isinstance(call.function, OperandIdentifier):
            index_val = self._interpreter.evaluate(call.function.index).value
            if isinstance(index_val, sympy.Basic):
                return self._emit_symbolic_lambda_list(call, index_val)
        function = self._interpreter.evaluate(call.function).as_type(FunctionClosure)
        args = call.positional_args
        with ErrorManager().call(function.name):
            self._emit_quantum_function_call(
                function, args, self._debug_info.get(call.uuid)
            )
        return True

    def _emit_symbolic_lambda_list(
        self, call: QuantumFunctionCall, index: sympy.Basic
    ) -> bool:
        if TYPE_CHECKING:
            assert isinstance(call.function, OperandIdentifier)
        funcs = self._interpreter.evaluate(call.function.name).value
        if not isinstance(funcs, list):
            raise ClassiqInternalExpansionError(
                f"Unexpected lambda list type {type(funcs).__name__!r}"
            )
        for stmt in self._create_recursive_if(call, index, len(funcs)):
            self._interpreter.emit(stmt)
        return True

    @staticmethod
    def _create_recursive_if(
        call: QuantumFunctionCall, index: sympy.Basic, num_funcs: int
    ) -> list[QuantumStatement]:
        if TYPE_CHECKING:
            assert isinstance(call.function, OperandIdentifier)
        stmt: list[QuantumStatement] = []
        for idx in reversed(range(num_funcs)):
            stmt = [
                ClassicalIf(
                    condition=Expression(expr=f"{index} == {idx}"),
                    then=[
                        QuantumFunctionCall(
                            function=OperandIdentifier(
                                name=call.function.name, index=Expression(expr=str(idx))
                            ),
                            positional_args=call.positional_args,
                        )
                    ],
                    else_=stmt,
                )
            ]
        return stmt


class DeclarativeQuantumFunctionCallEmitter(
    QuantumFunctionCallEmitter, DeclarativeCallEmitter
):
    pass
