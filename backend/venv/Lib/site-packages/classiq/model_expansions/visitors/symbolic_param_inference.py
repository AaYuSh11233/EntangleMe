import ast
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from itertools import chain, zip_longest
from typing import Optional, cast

from classiq.interface.generator.expressions.atomic_expression_functions import (
    CLASSICAL_ATTRIBUTES,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.helpers.pydantic_model_helpers import nameables_to_dict
from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
)
from classiq.interface.model.handle_binding import FieldHandleBinding, HandleBinding
from classiq.interface.model.model_visitor import ModelVisitor
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.quantum_function_call import ArgValue, QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    AnonPositionalArg,
    AnonQuantumOperandDeclaration,
    NamedParamsQuantumFunctionDeclaration,
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_lambda_function import (
    OperandIdentifier,
    QuantumLambdaFunction,
)

from classiq.model_expansions.visitors.variable_references import VarRefCollector


def handle_is_directly_used_var(handle: HandleBinding, scope_vars: set[str]) -> bool:
    return handle.name in scope_vars and (
        not isinstance(handle, FieldHandleBinding)
        or handle.field not in CLASSICAL_ATTRIBUTES
    )


def set_generative_recursively(classical_type: ClassicalType) -> None:
    if (
        isinstance(classical_type, TypeName)
        and classical_type.has_classical_struct_decl
    ):
        for field_type in classical_type.classical_struct_decl.variables.values():
            set_generative_recursively(field_type)
        return
    classical_type.set_generative()
    if isinstance(classical_type, ClassicalArray):
        set_generative_recursively(classical_type.element_type)
    if isinstance(classical_type, ClassicalTuple):
        for element_type in classical_type.element_types:
            set_generative_recursively(element_type)


def _get_expressions(arg: ArgValue) -> list[Expression]:
    if isinstance(arg, Expression):
        return [arg]
    if isinstance(arg, HandleBinding):
        return arg.expressions()
    if isinstance(arg, OperandIdentifier):
        return [arg.index]
    if isinstance(arg, list):
        return list(chain.from_iterable(_get_expressions(item) for item in arg))
    return []


def _get_param_expressions(param: AnonPositionalArg) -> list[Expression]:
    if isinstance(param, AnonClassicalParameterDeclaration):
        return param.classical_type.expressions
    if isinstance(param, AnonQuantumOperandDeclaration):
        return list(
            chain.from_iterable(
                _get_param_expressions(nested_param)
                for nested_param in param.positional_arg_declarations
            )
        )
    return param.quantum_type.expressions


class SymbolicParamInference(ModelVisitor):
    def __init__(
        self,
        functions: list[NativeFunctionDefinition],
        additional_signatures: Optional[
            list[NamedParamsQuantumFunctionDeclaration]
        ] = None,
    ) -> None:
        self._functions = nameables_to_dict(functions)
        self._additional_signatures = (
            {}
            if additional_signatures is None
            else nameables_to_dict(additional_signatures)
        )
        self._inferred_funcs: set[str] = set()
        self._scope: Mapping[str, ClassicalType] = {}
        self._scope_operands: dict[str, QuantumOperandDeclaration] = {}

    def infer(self) -> None:
        for func in self._functions.values():
            self._infer_func_params(func)

    @contextmanager
    def function_context(
        self,
        func_name: Optional[str],
        scope: Mapping[str, ClassicalType],
        scope_operands: dict[str, QuantumOperandDeclaration],
    ) -> Iterator[None]:
        prev_scope = self._scope
        self._scope = scope
        prev_scope_ops = self._scope_operands
        self._scope_operands = scope_operands
        yield
        self._scope = prev_scope
        self._scope_operands = prev_scope_ops

    def _infer_func_params(self, func: NativeFunctionDefinition) -> None:
        if func.name in self._inferred_funcs:
            return
        self._inferred_funcs.add(func.name)
        scope = {param.name: param.classical_type for param in func.param_decls}
        scope_operands = func.operand_declarations_dict
        with self.function_context(func.name, scope, scope_operands):
            for param in func.positional_arg_declarations:
                for expr in _get_param_expressions(param):
                    self._process_compile_time_expression(expr.expr)
            self.visit(func.body)

    def visit_QuantumLambdaFunction(self, func: QuantumLambdaFunction) -> None:
        func.set_op_decl(func.func_decl.model_copy(deep=True))
        scope = dict(self._scope) | {
            cast(str, param.name): param.classical_type
            for param in func.named_func_decl.param_decls
        }
        scope_operands = self._scope_operands | nameables_to_dict(
            cast(
                Sequence[QuantumOperandDeclaration],
                func.named_func_decl.operand_declarations,
            )
        )
        with self.function_context(None, scope, scope_operands):
            self.visit(func.body)

    def visit_QuantumFunctionCall(self, call: QuantumFunctionCall) -> None:
        self._process_compile_time_expressions(call.function)
        params = self._get_params(call)
        for param, arg in zip_longest(params, call.positional_args):
            if (
                not isinstance(param, AnonClassicalParameterDeclaration)
                or not param.classical_type.is_purely_declarative
            ):
                self._process_compile_time_expressions(arg)
            else:
                for expr in _get_expressions(arg):
                    self._process_nested_compile_time_expression(expr.expr)
        self.generic_visit(call)

    def _get_params(self, call: QuantumFunctionCall) -> Sequence[AnonPositionalArg]:
        name = call.func_name
        if name in self._scope_operands:
            return self._scope_operands[name].positional_arg_declarations
        elif name in self._functions:
            func = self._functions[name]
            self._infer_func_params(func)
            return func.positional_arg_declarations
        elif name in self._additional_signatures:
            return self._additional_signatures[name].positional_arg_declarations
        return call.func_decl.positional_arg_declarations

    def _process_compile_time_expressions(self, arg: ArgValue) -> None:
        for expr in _get_expressions(arg):
            self._process_compile_time_expression(expr.expr)

    def _process_compile_time_expression(self, expr: str) -> None:
        vrc = VarRefCollector(
            ignore_duplicated_handles=True, ignore_sympy_symbols=True, unevaluated=True
        )
        vrc.visit(ast.parse(expr))
        for handle in vrc.var_handles:
            if handle_is_directly_used_var(handle, set(self._scope)):
                set_generative_recursively(self._scope[handle.name])

    def _process_nested_compile_time_expression(self, expr: str) -> None:
        vrc = VarRefCollector(
            ignore_duplicated_handles=True, ignore_sympy_symbols=True, unevaluated=True
        )
        vrc.visit(ast.parse(expr))
        for handle in vrc.var_handles:
            for nested_expr in handle.expressions():
                self._process_compile_time_expression(nested_expr.expr)
        for handle in vrc.subscript_handles:
            self._process_compile_time_expression(str(handle))
