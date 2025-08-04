import inspect
import os

from pydantic import ValidationError

from classiq.interface.exceptions import ClassiqError
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.source_reference import SourceReference

from classiq.model_expansions.closure import FunctionClosure, GenerativeFunctionClosure
from classiq.model_expansions.interpreters.generative_interpreter import (
    GenerativeInterpreter,
)
from classiq.model_expansions.quantum_operations import BindEmitter
from classiq.model_expansions.quantum_operations.allocate import AllocateEmitter
from classiq.model_expansions.quantum_operations.quantum_function_call import (
    DeclarativeQuantumFunctionCallEmitter,
)
from classiq.model_expansions.scope import Scope
from classiq.qmod.model_state_container import QMODULE


class FrontendGenerativeInterpreter(GenerativeInterpreter):
    def emit_allocate(self, allocate: Allocate) -> None:
        AllocateEmitter(self, allow_symbolic_attrs=True).emit(allocate)

    def emit_bind(self, bind: BindOperation) -> None:
        BindEmitter(self, allow_symbolic_size=True).emit(bind)

    def emit_quantum_function_call(self, call: QuantumFunctionCall) -> None:
        DeclarativeQuantumFunctionCallEmitter(self).emit(call)

    def _get_main_closure(self, main_func: FunctionClosure) -> FunctionClosure:
        if isinstance(main_func, GenerativeFunctionClosure):
            return GenerativeFunctionClosure.create(
                name=main_func.name,
                positional_arg_declarations=main_func.positional_arg_declarations,
                scope=Scope(parent=self._top_level_scope),
                _depth=0,
                generative_blocks={"body": main_func.generative_blocks["body"]},
            )

        return super()._get_main_closure(main_func)

    def process_exception(self, e: Exception) -> None:
        if not isinstance(e, (ClassiqError, ValidationError)):
            frame = inspect.trace()[-1]
            module = inspect.getmodule(frame[0])
            if module is None or not module.__name__.startswith("classiq."):
                file_name = os.path.split(frame.filename)[-1]
                if (
                    frame.positions is not None
                    and frame.positions.lineno is not None
                    and frame.positions.col_offset is not None
                    and frame.positions.end_lineno is not None
                    and frame.positions.end_col_offset is not None
                ):
                    source_ref = SourceReference(
                        start_line=frame.positions.lineno - 1,
                        start_column=frame.positions.col_offset - 1,
                        end_line=frame.positions.end_lineno - 1,
                        end_column=frame.positions.end_col_offset - 1,
                        file_name=file_name,
                    )
                else:
                    source_ref = SourceReference(
                        start_line=frame.lineno - 1,
                        start_column=frame.lineno - 1,
                        end_line=-1,
                        end_column=-1,
                        file_name=file_name,
                    )
                e_str = f": {e}" if str(e) else ""
                self._error_manager.add_error(
                    f"{type(e).__name__}{e_str}",
                    source_ref=source_ref,
                    function=frame.function,
                )
                return

        super().process_exception(e)

    def add_purely_declarative_function(self, function: FunctionClosure) -> None:
        functions_to_add = [function.name] + QMODULE.function_dependencies[
            function.name
        ]
        for func in functions_to_add:
            if func not in self._expanded_functions and func in QMODULE.native_defs:
                self._expanded_functions[func] = QMODULE.native_defs[func]
                if func in QMODULE.functions_compilation_metadata:
                    self._expanded_functions_compilation_metadata[func] = (
                        QMODULE.functions_compilation_metadata[func]
                    )
