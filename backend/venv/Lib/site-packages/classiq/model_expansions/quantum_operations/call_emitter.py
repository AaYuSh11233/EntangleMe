from collections.abc import Sequence
from itertools import chain, combinations
from typing import (
    Any,
    Generic,
    Optional,
    cast,
)
from uuid import UUID

import sympy

from classiq.interface.debug_info.debug_info import (
    FunctionDebugInfo,
    calculate_port_to_passed_variable_mapping,
)
from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.types.compilation_metadata import CompilationMetadata
from classiq.interface.helpers.backward_compatibility import zip_strict
from classiq.interface.helpers.text_utils import are, readable_list, s
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.model import MAIN_FUNCTION_NAME
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_call import ArgValue, QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
    PositionalArg,
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_statement import QuantumStatement
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)

from classiq.evaluators.argument_types import (
    add_information_from_output_arguments,
    handle_args_numeric_bounds,
)
from classiq.evaluators.parameter_types import (
    evaluate_parameter_types_from_args,
)
from classiq.model_expansions.capturing.captured_vars import (
    INITIALIZED_VAR_MESSAGE,
    UNINITIALIZED_VAR_MESSAGE,
    validate_args_are_not_propagated,
)
from classiq.model_expansions.closure import Closure, FunctionClosure
from classiq.model_expansions.function_builder import (
    FunctionContext,
)
from classiq.model_expansions.quantum_operations.emitter import (
    Emitter,
    QuantumStatementT,
)
from classiq.model_expansions.quantum_operations.function_calls_cache import (
    get_func_call_cache_key,
)
from classiq.model_expansions.scope import (
    Evaluated,
    QuantumSymbol,
    QuantumSymbolList,
    QuantumVariable,
    Scope,
)
from classiq.model_expansions.transformers.model_renamer import ModelRenamer
from classiq.model_expansions.transformers.type_modifier_inference import (
    TypeModifierValidation,
)
from classiq.qmod.pretty_print.expression_to_python import transform_expression
from classiq.qmod.semantics.validation.signature_validation import (
    validate_function_signature,
)


def _validate_cloning(evaluated_args: list[Evaluated]) -> None:
    handles = chain.from_iterable(
        (
            [arg.value.handle]
            if isinstance(arg.value, QuantumSymbol)
            else arg.value.handles if isinstance(arg.value, QuantumSymbolList) else []
        )
        for arg in evaluated_args
    )
    for handle, other_handle in combinations(handles, 2):
        if handle.overlaps(other_handle):
            if handle == other_handle:
                raise ClassiqExpansionError(
                    f"Quantum cloning violation: Argument {str(handle)!r} is "
                    f"duplicated"
                )
            raise ClassiqExpansionError(
                f"Quantum cloning violation: Arguments {str(handle)!r} and "
                f"{str(other_handle)!r} overlap"
            )


def _is_symbolic(arg: Any) -> bool:
    if isinstance(arg, (ClassicalProxy, AnyClassicalValue)):
        return True
    if isinstance(arg, list):
        return any(_is_symbolic(item) for item in arg)
    if isinstance(arg, QmodStructInstance):
        return any(_is_symbolic(item) for item in arg.fields.values())
    if isinstance(arg, sympy.Basic):
        return len(arg.free_symbols) > 0
    return False


def _validate_gen_args(
    function: FunctionClosure, evaluated_args: list[Evaluated]
) -> None:
    for param, arg in zip_strict(
        function.positional_arg_declarations, evaluated_args, strict=True
    ):
        if (
            isinstance(param, ClassicalParameterDeclaration)
            and not param.classical_type.is_purely_declarative
            and _is_symbolic(arg.value)
        ):
            readable_expr = transform_expression(str(arg.value), {}, {}, one_line=True)
            raise ClassiqExpansionError(
                f"Cannot pass symbolic expression {readable_expr!r} as Python-type "
                f"parameter {param.name!r}"
            )


class CallEmitter(Generic[QuantumStatementT], Emitter[QuantumStatementT], ModelRenamer):
    @staticmethod
    def _should_wrap(body: Sequence[QuantumStatement]) -> bool:
        # This protects shadowing of captured variables (i.e, bad user code) by wrapping the body in a function
        # I'm sure there are better ways to handle it, but this is the simplest way to do it for now
        return any(isinstance(stmt, VariableDeclarationStatement) for stmt in body)

    def _create_expanded_wrapping_function(
        self,
        name: str,
        body: Sequence[QuantumStatement],
        debug_info: Optional[FunctionDebugInfo] = None,
    ) -> QuantumFunctionCall:
        wrapping_function = FunctionClosure.create(
            name=self._counted_name_allocator.allocate(name),
            body=body,
            scope=Scope(parent=self._current_scope),
            lambda_external_vars=self._builder.current_block.captured_vars,
        )
        return self._create_quantum_function_call(wrapping_function, list(), debug_info)

    def _emit_quantum_function_call(
        self,
        function: FunctionClosure,
        args: list[ArgValue],
        propagated_debug_info: Optional[FunctionDebugInfo],
    ) -> QuantumFunctionCall:
        call = self._create_quantum_function_call(
            function, args, propagated_debug_info=propagated_debug_info
        )
        self.emit_statement(call)
        return call

    @staticmethod
    def _get_back_ref(
        propagated_debug_info: Optional[FunctionDebugInfo],
    ) -> Optional[UUID]:
        if propagated_debug_info is None:
            return None
        if propagated_debug_info.node is None:
            return None
        return propagated_debug_info.node.uuid

    def _create_quantum_function_call(
        self,
        function: FunctionClosure,
        args: list[ArgValue],
        propagated_debug_info: Optional[FunctionDebugInfo],
    ) -> QuantumFunctionCall:
        function = function.clone()
        function = function.set_depth(self._builder.current_function.depth + 1)
        self._validate_call_args(function.positional_arg_declarations, args)
        evaluated_args = [self._interpreter.evaluate(arg) for arg in args]
        _validate_cloning(evaluated_args)
        new_declaration = self._prepare_fully_typed_declaration(
            function, evaluated_args
        )
        new_positional_arg_decls = new_declaration.positional_arg_declarations
        if not self.should_expand_function(function, evaluated_args):
            new_declaration = self._expanded_functions_by_name.get(
                function.name, new_declaration
            )
        else:
            _validate_gen_args(function, evaluated_args)
            new_declaration = self._expand_function(
                evaluated_args, new_declaration, function
            )
            new_positional_arg_decls = new_declaration.positional_arg_declarations
            evaluated_args = [
                arg
                for param, arg in zip_strict(
                    function.positional_arg_declarations, evaluated_args, strict=True
                )
                if isinstance(arg.value, QuantumVariable)
                or (
                    isinstance(param, ClassicalParameterDeclaration)
                    and param.classical_type.is_purely_declarative
                )
            ]

        add_information_from_output_arguments(new_positional_arg_decls, evaluated_args)
        handle_args_numeric_bounds(new_positional_arg_decls, evaluated_args)
        captured_args = function.captured_vars.filter_vars(function).get_captured_args(
            self._builder.current_function
        )
        new_positional_args = [
            arg.emit(param)
            for param, arg in zip_strict(
                new_positional_arg_decls[
                    : len(new_positional_arg_decls) - len(captured_args)
                ],
                evaluated_args,
                strict=True,
            )
        ]
        validate_args_are_not_propagated(
            new_positional_args,
            captured_args,
            lambda vars: f"Argument{s(vars)} {readable_list(vars)} {are(vars)} used in adjacent lambda functions",
        )
        new_positional_args.extend(captured_args)
        new_call = QuantumFunctionCall(
            function=new_declaration.name,
            positional_args=new_positional_args,
            back_ref=self._get_back_ref(propagated_debug_info),
        )

        port_to_passed_variable_map = calculate_port_to_passed_variable_mapping(
            new_positional_arg_decls,
            [
                arg.value.handle if isinstance(arg.value, QuantumSymbol) else None
                for arg in evaluated_args
            ],
        )
        self._debug_info[new_call.uuid] = FunctionDebugInfo(
            name=new_call.func_name,
            port_to_passed_variable_map=port_to_passed_variable_map,
            node=new_call._as_back_ref(),
        )
        new_call.set_func_decl(new_declaration)
        return new_call

    def should_expand_function(
        self, function: FunctionClosure, args: list[Evaluated]
    ) -> bool:
        return not function.is_atomic

    def _expand_function(
        self,
        args: list[Evaluated],
        decl: NamedParamsQuantumFunctionDeclaration,
        function: FunctionClosure,
    ) -> NamedParamsQuantumFunctionDeclaration:
        inferred_args = self._add_params_to_scope(
            decl.positional_arg_declarations, args, function
        )
        function = function.with_new_declaration(decl)
        cache_key = get_func_call_cache_key(decl, inferred_args)
        if cache_key in self._expanded_functions:
            function_def = self._expanded_functions[cache_key]
            self._expand_cached_function(function, function_def)
            self._expanded_functions_compilation_metadata[
                function_def.name
            ].occurrences_number += 1
            return function_def

        context = self._expand_operation(function)
        function_context = cast(FunctionContext, context)
        function_def = self._create_function_definition(function_context, args)
        self._validate_type_modifiers(function_context, function_def)
        self._expanded_functions[cache_key] = function_def
        self._top_level_scope[function_def.name] = Evaluated(
            value=function_context.closure.with_new_declaration(function_def)
        )
        compilation_metadata = self._functions_compilation_metadata.get(function.name)
        if compilation_metadata is not None:
            self._expanded_functions_compilation_metadata[function_def.name] = (
                compilation_metadata
            )
        return function_def

    def _create_function_definition(
        self, function_context: FunctionContext, args: list[Evaluated]
    ) -> NativeFunctionDefinition:
        params = [
            param
            for arg, param in zip(args, function_context.positional_arg_declarations)
            if isinstance(param, PortDeclaration)
            or (
                isinstance(param, ClassicalParameterDeclaration)
                and param.classical_type.is_purely_declarative
            )
        ]
        func_def = self._builder.create_definition(function_context, params)

        captured_vars = function_context.closure.captured_vars.filter_vars(
            function_context.closure
        )
        captured_ports = captured_vars.get_captured_parameters()
        if len(captured_ports) == 0:
            return func_def
        func_def.positional_arg_declarations = list(
            chain.from_iterable((func_def.positional_arg_declarations, captured_ports))
        )

        rewrite_mapping = captured_vars.get_captured_mapping(function_context.is_lambda)
        func_def.body = self.rewrite(func_def.body, rewrite_mapping)

        return func_def

    @staticmethod
    def _add_params_to_scope(
        parameters: Sequence[PositionalArg],
        arguments: Sequence[Evaluated],
        closure: FunctionClosure,
    ) -> list[Evaluated]:
        inferred_args: list[Evaluated] = []
        for parameter, argument in zip(parameters, arguments):
            param_handle = HandleBinding(name=parameter.name)
            if isinstance(argument.value, QuantumVariable):
                assert isinstance(parameter, PortDeclaration)
                inferred_arg = Evaluated(
                    QuantumSymbol(
                        handle=param_handle,
                        quantum_type=parameter.quantum_type,
                    ),
                    defining_function=closure,
                )
            elif (
                isinstance(parameter, ClassicalParameterDeclaration)
                and parameter.classical_type.is_purely_declarative
            ):
                inferred_arg = Evaluated(
                    value=parameter.classical_type.get_classical_proxy(param_handle),
                    defining_function=closure,
                )
            else:
                inferred_arg = argument
            closure.scope[parameter.name] = inferred_arg
            inferred_args.append(inferred_arg)
        return inferred_args

    def _prepare_fully_typed_declaration(
        self, function: FunctionClosure, evaluated_args: list[Evaluated]
    ) -> NamedParamsQuantumFunctionDeclaration:
        """
        Given, for example,
        def my_func(x: int, q: QArray["x"], p: QArray[]) -> None:
        ...
        def main(...):
            ...
            allocate(5, s)
            my_func(3, r, s)
        The code below will evaluate x to be 3, q to be of size 3 and p to be of size 5.
        Note that it requires a scope for the parameter declaration space, which is
        different from the call scope. For example, the former uses r,s and the latter
        uses p, q.
        """
        validate_function_signature(function.positional_arg_declarations)
        # The signature scope is passed as a separate argument to avoid contaminating the statement execution scope
        return NamedParamsQuantumFunctionDeclaration(
            name=function.name,
            positional_arg_declarations=evaluate_parameter_types_from_args(
                function,
                function.signature_scope,
                evaluated_args,
            ),
        )

    def _validate_call_args(
        self, params: Sequence[PositionalArg], args: list[ArgValue]
    ) -> None:
        for param, arg in zip(params, args):
            if not isinstance(param, PortDeclaration) or not isinstance(
                arg, HandleBinding
            ):
                continue
            var_name = arg.name
            symbol = self._interpreter.evaluate(var_name)
            if (
                not isinstance(symbol.value, QuantumSymbol)
                or symbol.defining_function is None
            ):
                continue
            var_state = self._builder.current_block.captured_vars.get_state(
                var_name, symbol.defining_function
            )
            if not var_state and param.direction in (
                PortDeclarationDirection.Inout,
                PortDeclarationDirection.Input,
            ):
                raise ClassiqExpansionError(UNINITIALIZED_VAR_MESSAGE.format(var_name))
            if var_state and param.direction == PortDeclarationDirection.Output:
                raise ClassiqExpansionError(INITIALIZED_VAR_MESSAGE.format(var_name))

    def _validate_type_modifiers(
        self, func_context: FunctionContext, func_def: NativeFunctionDefinition
    ) -> None:
        if self._should_override_type_modifiers(func_context):
            self._override_type_modifiers(func_def)

        unchecked = self._functions_compilation_metadata.get(
            func_context.name, CompilationMetadata()
        ).unchecked
        TypeModifierValidation(
            skip_validation=self._interpreter.skip_type_modifier_validation
        ).run(func_def, unchecked)

    @staticmethod
    def _should_override_type_modifiers(func_context: FunctionContext) -> bool:
        """
        The type modifier can be changed according to the operand passed to the
        function. For example,
        apply_to_all(X, q) --> q will be Permutable after expansion
        apply_to_all(H, q) --> q will be Quantum after expansion
        This also holds for the intermediate lambda created during the expansion.

        We don't override the type modifier if it's explicitly specified (Permutable or
        Const), neither in the function declaration nor in the operand declaration.
        """

        if func_context.is_lambda:
            return True

        orig_name = func_context.name
        if (
            orig_name == MAIN_FUNCTION_NAME
            or orig_name not in func_context.closure.scope
        ):
            return False

        orig_func = func_context.closure.scope[orig_name].value
        return not (
            isinstance(orig_func, Closure)
            and not any(
                isinstance(param_decl, QuantumOperandDeclaration)
                for param_decl in orig_func.positional_arg_declarations
            )
        )

    @staticmethod
    def _override_type_modifiers(func_def: NativeFunctionDefinition) -> None:
        # only override the modifier if it's unspecified (not Permutable or Const)
        for port in func_def.port_declarations:
            if port.type_modifier is TypeModifier.Mutable:
                port.type_modifier = TypeModifier.Inferred
