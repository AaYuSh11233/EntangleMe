import ast
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from contextlib import nullcontext
from functools import singledispatchmethod
from typing import Any, cast

from pydantic import ValidationError

from classiq.interface.debug_info.debug_info import (
    new_function_debug_info_by_node,
)
from classiq.interface.exceptions import (
    ClassiqError,
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.atomic_expression_functions import (
    CLASSICAL_ATTRIBUTES,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.types.compilation_metadata import CompilationMetadata
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
    HandlesList,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.model import MAIN_FUNCTION_NAME, Model
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.quantum_function_declaration import (
    QuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_lambda_function import (
    OperandIdentifier,
    QuantumLambdaFunction,
)
from classiq.interface.model.quantum_statement import QuantumStatement

from classiq.evaluators.classical_expression import (
    evaluate_classical_expression,
)
from classiq.model_expansions.closure import (
    Closure,
    FunctionClosure,
)
from classiq.model_expansions.debug_flag import debug_mode
from classiq.model_expansions.function_builder import (
    FunctionContext,
    OperationBuilder,
    OperationContext,
)
from classiq.model_expansions.scope import (
    Evaluated,
    QuantumSymbol,
    QuantumSymbolList,
    Scope,
)
from classiq.model_expansions.scope_initialization import (
    add_entry_point_params_to_scope,
    init_builtin_types,
    init_top_level_scope,
)
from classiq.model_expansions.utils.counted_name_allocator import CountedNameAllocator
from classiq.model_expansions.visitors.variable_references import VarRefCollector
from classiq.qmod.builtins.constants import __all__ as builtin_constants
from classiq.qmod.builtins.enums import BUILTIN_ENUM_DECLARATIONS
from classiq.qmod.builtins.structs import BUILTIN_STRUCT_DECLARATIONS
from classiq.qmod.model_state_container import QMODULE
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator
from classiq.qmod.semantics.error_manager import ErrorManager
from classiq.qmod.semantics.validation.model_validation import validate_model
from classiq.qmod.utilities import qmod_val_to_expr_str


class BaseInterpreter:
    skip_type_modifier_validation: bool = False

    def __init__(self, model: Model) -> None:
        validate_model(model)
        self._model = model
        self._top_level_scope = Scope()
        self._counted_name_allocator = CountedNameAllocator()
        self._builder = OperationBuilder(
            self._top_level_scope, self._counted_name_allocator
        )
        self._expanded_functions: dict[str, NativeFunctionDefinition] = {}

        init_builtin_types()
        init_top_level_scope(model, self._top_level_scope)
        QStructAnnotator().visit(
            ClassicalFunctionDeclaration.FOREIGN_FUNCTION_DECLARATIONS
        )
        self._functions_compilation_metadata: dict[str, CompilationMetadata] = dict(
            self._model.functions_compilation_metadata
        )
        self._expanded_functions_compilation_metadata: dict[
            str, CompilationMetadata
        ] = defaultdict(CompilationMetadata)
        self._counted_name_allocator = CountedNameAllocator()
        self._error_manager: ErrorManager = ErrorManager()

    def _expand_main_func(self) -> None:
        main_closure = self._get_main_closure(
            self._top_level_scope[MAIN_FUNCTION_NAME].value
        )
        add_entry_point_params_to_scope(
            main_closure.positional_arg_declarations, main_closure
        )
        context = self._expand_operation(main_closure)
        self._expanded_functions[main_closure.name] = self._builder.create_definition(
            cast(FunctionContext, context), main_closure.positional_arg_declarations
        )

    def _get_main_closure(self, main_func: FunctionClosure) -> FunctionClosure:
        return FunctionClosure.create(
            name=main_func.name,
            positional_arg_declarations=main_func.positional_arg_declarations,
            scope=Scope(parent=self._top_level_scope),
            _depth=0,
            body=main_func.body,
        )

    def expand(self) -> Model:
        try:
            with self._error_manager.call("main"):
                self._expand_main_func()
        except Exception as e:
            if isinstance(e, ClassiqInternalExpansionError) or debug_mode.get():
                raise e
            self.process_exception(e)
        finally:
            self._error_manager.report_errors(ClassiqExpansionError)

        return Model(
            constraints=self._model.constraints,
            preferences=self._model.preferences,
            classical_execution_code=self._model.classical_execution_code,
            execution_preferences=self._model.execution_preferences,
            functions=list(self._expanded_functions.values()),
            constants=[
                const
                for name, const in QMODULE.constants.items()
                if name not in builtin_constants
            ],
            enums=[
                enum_decl
                for name, enum_decl in QMODULE.enum_decls.items()
                if name not in BUILTIN_ENUM_DECLARATIONS
            ],
            types=[
                struct_decl
                for name, struct_decl in QMODULE.type_decls.items()
                if name not in BUILTIN_STRUCT_DECLARATIONS
            ],
            qstructs=list(QMODULE.qstruct_decls.values()),
            debug_info=self._model.debug_info,
            functions_compilation_metadata=self._expanded_functions_compilation_metadata,
        )

    def process_exception(self, e: Exception) -> None:
        if not isinstance(e, (ClassiqError, ValidationError)):
            raise ClassiqInternalExpansionError(str(e)) from e
        prefix = ""
        if not isinstance(e, ClassiqExpansionError):
            prefix = f"{type(e).__name__}: "
        self._error_manager.add_error(f"{prefix}{e}")

    @singledispatchmethod
    def evaluate(self, expression: Any) -> Evaluated:
        raise NotImplementedError(f"Cannot evaluate {expression!r}")

    @evaluate.register
    def evaluate_classical_expression(self, expression: Expression) -> Evaluated:
        expr = evaluate_classical_expression(expression, self._builder.current_scope)
        vrc = VarRefCollector(ignore_duplicated_handles=True, unevaluated=True)
        vrc.visit(ast.parse(qmod_val_to_expr_str(expr.value)))
        for handle in vrc.var_handles:
            if handle.name in self._builder.current_scope and isinstance(
                self._builder.current_scope[handle.name].value, QuantumSymbol
            ):
                if (
                    isinstance(handle, FieldHandleBinding)
                    and handle.field in CLASSICAL_ATTRIBUTES
                ):
                    handle = handle.base_handle
                self.evaluate(handle)
        return expr

    @evaluate.register
    def evaluate_identifier(self, identifier: str) -> Evaluated:
        return self._builder.current_scope[identifier]

    @evaluate.register
    def _evaluate_lambda(self, function: QuantumLambdaFunction) -> Evaluated:
        return self.evaluate_lambda(function)

    def evaluate_lambda(self, function: QuantumLambdaFunction) -> Evaluated:
        raise NotImplementedError

    @evaluate.register
    def evaluate_handle_binding(self, handle_binding: HandleBinding) -> Evaluated:
        return self.evaluate(handle_binding.name)

    @evaluate.register
    def evaluate_sliced_handle_binding(
        self, sliced_handle_binding: SlicedHandleBinding
    ) -> Evaluated:
        quantum_variable = self.evaluate(sliced_handle_binding.base_handle).as_type(
            QuantumSymbol
        )
        start = self.evaluate(sliced_handle_binding.start).value
        end = self.evaluate(sliced_handle_binding.end).value
        return Evaluated(value=quantum_variable[start:end])

    @evaluate.register
    def evaluate_list(self, value: list) -> Evaluated:
        return Evaluated(value=[self.evaluate(arg).value for arg in value])

    @evaluate.register
    def evaluate_subscript_handle(self, subscript: SubscriptHandleBinding) -> Evaluated:
        base_value = self.evaluate(subscript.base_handle)
        index_value = self.evaluate(subscript.index).value
        return Evaluated(value=base_value.value[index_value])

    @evaluate.register
    def evaluate_subscript_operand(self, subscript: OperandIdentifier) -> Evaluated:
        base_value = self.evaluate(subscript.name)
        index_value = self.evaluate(subscript.index).as_type(int)
        return Evaluated(value=base_value.value[index_value])

    @evaluate.register
    def evaluate_field_access(self, field_access: FieldHandleBinding) -> Evaluated:
        base_value = self.evaluate(field_access.base_handle).as_type(QuantumSymbol)
        fields = base_value.fields
        field_name = field_access.field
        if field_name not in fields:
            raise ClassiqExpansionError(
                f"Struct {base_value.quantum_type.type_name} has no field "
                f"{field_name!r}. Available fields: {', '.join(fields.keys())}"
            )
        return Evaluated(value=fields[field_name])

    @evaluate.register
    def evaluate_handles_list(self, handles_list: HandlesList) -> Evaluated:
        return Evaluated(
            value=QuantumSymbolList.from_symbols(
                [self.evaluate(handle).value for handle in handles_list.handles]
            )
        )

    @abstractmethod
    def emit(self, statement: QuantumStatement) -> None:
        pass

    def _expand_block(self, block: Sequence[QuantumStatement], block_name: str) -> None:
        with self._builder.block_context(block_name):
            for statement in block:
                self.emit_statement(statement)

    def emit_statement(self, statement: QuantumStatement) -> None:
        source_ref = statement.source_ref
        error_context = (
            self._error_manager.node_context(statement)
            if source_ref is not None
            else nullcontext()
        )
        self.add_to_debug_info(statement)
        with error_context, self._builder.source_ref_context(source_ref):
            self.emit(statement)

    def add_to_debug_info(self, statement: QuantumStatement) -> None:
        if statement.uuid not in self._model.debug_info:
            self._model.debug_info[statement.uuid] = new_function_debug_info_by_node(
                statement  # type: ignore[arg-type]
            )

    def _expand_operation(self, operation: Closure) -> OperationContext:
        with self._builder.operation_context(operation) as context:
            self._expand_body(operation)

        return context

    def _expand_cached_function(
        self, operation: FunctionClosure, func_def: NativeFunctionDefinition
    ) -> None:
        with self._builder.operation_context(operation):
            cached_closure = self._top_level_scope[func_def.name].value
            operation.captured_vars.set(
                cached_closure.captured_vars, cached_closure, operation
            )

    def _expand_body(self, operation: Closure) -> None:
        for block, block_body in operation.blocks.items():
            self._expand_block(block_body, block)

    def _get_function_declarations(self) -> Sequence[QuantumFunctionDeclaration]:
        return [
            QuantumFunctionDeclaration(
                name=func_closure.name,
                positional_arg_declarations=func_closure.positional_arg_declarations,
            )
            for func in self._top_level_scope.values()
            if isinstance(func_closure := func.value, FunctionClosure)
        ]
