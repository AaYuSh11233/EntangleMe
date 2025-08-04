from itertools import chain
from typing import TYPE_CHECKING

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.quantum_type import QuantumBitvector, QuantumNumeric

from classiq.evaluators.parameter_types import (
    evaluate_types_in_quantum_symbols,
)
from classiq.evaluators.qmod_type_inference.quantum_type_inference import (
    inject_quantum_type_attributes_inplace,
)
from classiq.evaluators.quantum_type_utils import (
    validate_bind_targets,
)
from classiq.model_expansions.quantum_operations.emitter import Emitter
from classiq.model_expansions.scope import Evaluated, QuantumSymbol

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class BindEmitter(Emitter[BindOperation]):
    def __init__(
        self, interpreter: "BaseInterpreter", allow_symbolic_size: bool = False
    ) -> None:
        super().__init__(interpreter)
        self._allow_symbolic_size = allow_symbolic_size

    def emit(self, bind: BindOperation, /) -> bool:
        inputs, outputs = self._get_inputs_outputs(bind)
        if not self._allow_symbolic_size:
            validate_bind_targets(bind, self._current_scope)
        self._process_var_sizes(bind, inputs, outputs)

        for symbol in chain(inputs, outputs):
            if isinstance(symbol.quantum_type, QuantumNumeric):
                symbol.quantum_type.reset_bounds()

        self.emit_statement(
            BindOperation(
                in_handles=bind.in_handles,
                out_handles=bind.out_handles,
                back_ref=bind.uuid,
            )
        )
        return True

    def _get_inputs_outputs(
        self, bind: BindOperation
    ) -> tuple[list[QuantumSymbol], list[QuantumSymbol]]:
        evaluated_inputs: list[Evaluated] = [
            self._interpreter.evaluate(arg) for arg in bind.in_handles
        ]
        evaluated_outputs: list[Evaluated] = [
            self._interpreter.evaluate(arg) for arg in bind.out_handles
        ]
        self._validate_handle_states(evaluated_inputs, evaluated_outputs)
        inputs: list[QuantumSymbol] = [
            input.as_type(QuantumSymbol) for input in evaluated_inputs
        ]
        outputs: list[QuantumSymbol] = [
            output.as_type(QuantumSymbol) for output in evaluated_outputs
        ]
        inputs = evaluate_types_in_quantum_symbols(inputs, self._current_scope)
        outputs = evaluate_types_in_quantum_symbols(outputs, self._current_scope)
        return inputs, outputs

    def _validate_handle_states(
        self, inputs: list[Evaluated], outputs: list[Evaluated]
    ) -> None:
        input_var_names: set[str] = set()
        for inp in inputs:
            if inp.defining_function is None:
                raise ClassiqInternalExpansionError
            var_name = inp.value.handle.name
            input_var_names.add(var_name)
            state = self._builder.current_block.captured_vars.get_state(
                var_name, inp.defining_function
            )
            if not state:
                raise ClassiqExpansionError(
                    f"Cannot use uninitialized quantum variable "
                    f"{inp.value.handle.name!r} on the left-hand side of a bind "
                    f"statement"
                )
        for out in outputs:
            if out.defining_function is None:
                raise ClassiqInternalExpansionError
            var_name = out.value.handle.name
            if var_name in input_var_names:
                continue
            state = self._builder.current_block.captured_vars.get_state(
                var_name, out.defining_function
            )
            if state:
                raise ClassiqExpansionError(
                    f"Cannot use initialized quantum variable "
                    f"{out.value.handle.name!r} on the right-hand side of a bind "
                    f"statement"
                )

    def _process_var_sizes(
        self,
        bind: BindOperation,
        inputs: list[QuantumSymbol],
        outputs: list[QuantumSymbol],
    ) -> None:
        unsized_inputs = [
            input for input in inputs if not input.quantum_type.has_size_in_bits
        ]
        if len(unsized_inputs) > 0:
            if self._allow_symbolic_size:
                return
            raise ClassiqInternalExpansionError("Uninitialized bind inputs")

        unsized_outputs = [
            output for output in outputs if not output.quantum_type.has_size_in_bits
        ]
        if len(unsized_outputs) > 1:
            if self._allow_symbolic_size:
                return
            raise ClassiqExpansionError(
                f"Cannot perform the split operation {bind.in_handles[0].name} -> {{{', '.join(out_handle.name for out_handle in bind.out_handles)}}}:\n"
                f"Quantum variables {', '.join(str(out_handle.handle) for out_handle in unsized_outputs)} are used as bind outputs, but their size cannot be inferred."
            )

        input_size = sum(input.quantum_type.size_in_bits for input in inputs)
        output_size = sum(
            output.quantum_type.size_in_bits
            for output in outputs
            if output.quantum_type.has_size_in_bits
        )
        if len(unsized_outputs) == 1:
            unsized_type = unsized_outputs[0].quantum_type
            new_size = input_size - output_size
            if not inject_quantum_type_attributes_inplace(
                QuantumBitvector(length=Expression(expr=str(new_size))), unsized_type
            ):
                raise ClassiqExpansionError(
                    f"Cannot bind {new_size} qubits to variable "
                    f"{str(unsized_outputs[0])!r} of type "
                    f"{unsized_type.qmod_type_name}"
                )
        elif input_size != output_size:
            raise ClassiqExpansionError(
                f"The total size for the input and output of the bind operation must be the same. The in size is {input_size} and the out size is {output_size}"
            )
