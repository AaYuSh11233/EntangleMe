from typing import TYPE_CHECKING, Union

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.functions.classical_type import ClassicalType
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_type import QuantumType
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)

from classiq.evaluators.parameter_types import (
    evaluate_type_in_classical_symbol,
    evaluate_type_in_quantum_symbol,
)
from classiq.model_expansions.quantum_operations.emitter import Emitter
from classiq.model_expansions.scope import ClassicalSymbol, Evaluated, QuantumSymbol


class VariableDeclarationStatementEmitter(Emitter[VariableDeclarationStatement]):
    def emit(self, variable_declaration: VariableDeclarationStatement, /) -> bool:
        var_decl = variable_declaration.model_copy(
            update=dict(back_ref=variable_declaration.uuid)
        )
        var_decl.qmod_type = variable_declaration.qmod_type.model_copy()
        if variable_declaration.name in self._current_scope:
            raise ClassiqExpansionError(
                f"Variable {variable_declaration.name!r} is already defined"
            )
        var_value: Union[QuantumSymbol, ClassicalSymbol]
        if variable_declaration.is_quantum:
            if TYPE_CHECKING:
                assert isinstance(var_decl.qmod_type, QuantumType)
            var_value = QuantumSymbol(
                handle=HandleBinding(name=var_decl.name),
                quantum_type=evaluate_type_in_quantum_symbol(
                    var_decl.qmod_type,
                    self._current_scope,
                    var_decl.name,
                ),
            )
            self._builder.current_block.captured_vars.init_var(
                var_decl.name, self._builder.current_function
            )
        else:
            if TYPE_CHECKING:
                assert isinstance(var_decl.qmod_type, ClassicalType)
            var_value = ClassicalSymbol(
                handle=HandleBinding(name=var_decl.name),
                classical_type=evaluate_type_in_classical_symbol(
                    var_decl.qmod_type,
                    self._current_scope,
                    var_decl.name,
                ),
            )
        self._current_scope[variable_declaration.name] = Evaluated(
            value=var_value, defining_function=self._builder.current_function
        )
        self.emit_statement(var_decl)
        return True
