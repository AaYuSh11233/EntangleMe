import ast
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cmp_to_key
from typing import TypeVar, cast

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.evaluated_expression import (
    EvaluatedExpression,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.visitor import NodeType
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.model_visitor import ModelTransformer
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumExpressionOperation,
)

from classiq.model_expansions.visitors.variable_references import VarRefCollector

AST_NODE = TypeVar("AST_NODE", bound=NodeType)


def _replace_full_word(pattern: str, substitution: str, target: str) -> str:
    return re.sub(
        rf"(^|\b|\W)({re.escape(pattern)})($|\b|\W)", rf"\1{substitution}\3", target
    )


def _handle_contains_handle(handle: HandleBinding, other_handle: HandleBinding) -> int:
    if str(other_handle) in str(handle) or other_handle.qmod_expr in handle.qmod_expr:
        return 1
    if str(handle) in str(other_handle) or handle.qmod_expr in other_handle.qmod_expr:
        return -1
    return 0


class ExprNormalizer(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.AST:
        if not isinstance(node.func, ast.Name):
            return self.generic_visit(node)
        if node.func.id == "get_field":
            if (
                len(node.args) != 2
                or not isinstance(node.args[1], ast.Constant)
                or not isinstance(node.args[1].value, str)
            ):
                raise ClassiqInternalExpansionError("Unexpected 'get_field' arguments")
            return ast.Attribute(
                value=self.visit(node.args[0]), attr=node.args[1].value
            )
        if node.func.id == "do_subscript":
            if len(node.args) != 2:
                raise ClassiqInternalExpansionError(
                    "Unexpected 'do_subscript' arguments"
                )
            return ast.Subscript(
                value=self.visit(node.args[0]), slice=self.visit(node.args[1])
            )
        return self.generic_visit(node)


@dataclass(frozen=True)
class HandleRenaming:
    source_handle: HandleBinding
    target_var_name: str

    @property
    def target_var_handle(self) -> HandleBinding:
        return HandleBinding(name=self.target_var_name)


SymbolRenaming = Mapping[HandleBinding, Sequence[HandleRenaming]]


def rewrite_expression(
    symbol_mapping: SymbolRenaming, expression: Expression
) -> Expression:
    normalized_expr = ExprNormalizer().visit(ast.parse(expression.expr))
    vrc = VarRefCollector(
        ignore_duplicated_handles=True, ignore_sympy_symbols=True, unevaluated=True
    )
    vrc.visit(normalized_expr)

    handle_names = {
        part.source_handle: part.target_var_handle
        for source, parts in symbol_mapping.items()
        if source.name in expression.expr
        for part in parts
    }
    new_expr_str = ast.unparse(normalized_expr)
    sorted_handles = sorted(
        vrc.var_handles,
        key=cmp_to_key(  # type:ignore[misc]
            lambda handle, other_handle: _handle_contains_handle(other_handle, handle)
        ),
    )
    for handle in sorted_handles:
        new_handle = handle.collapse()
        for handle_to_replace, replacement in handle_names.items():
            if new_handle.name == handle_to_replace.name:
                new_handle = new_handle.replace_prefix(handle_to_replace, replacement)
        new_expr_str = _replace_full_word(str(handle), str(new_handle), new_expr_str)

    new_expr = Expression(expr=new_expr_str)
    if not new_expr.is_evaluated():
        new_expr._evaluated_expr = EvaluatedExpression(
            value=AnyClassicalValue(new_expr_str)
        )
    return new_expr


class _ReplaceSplitVarsHandles(ModelTransformer):
    def __init__(self, symbol_mapping: SymbolRenaming) -> None:
        self._handle_replacements = {
            part.source_handle: part.target_var_handle
            for parts in symbol_mapping.values()
            for part in parts
        }

    def visit_HandleBinding(self, handle: HandleBinding) -> HandleBinding:
        handle = handle.collapse()
        for handle_to_replace, replacement in self._handle_replacements.items():
            handle = handle.replace_prefix(handle_to_replace, replacement)
        return handle


class _ReplaceSplitVarsExpressions(ModelTransformer):
    def __init__(self, symbol_mapping: SymbolRenaming) -> None:
        self._symbol_mapping = symbol_mapping

    def visit_Expression(self, expr: Expression) -> Expression:
        return rewrite_expression(self._symbol_mapping, expr)

    def visit_QuantumExpressionOperation(
        self, op: QuantumExpressionOperation
    ) -> QuantumExpressionOperation:
        op = cast(QuantumExpressionOperation, self.generic_visit(op))
        previous_var_handles = list(op._var_handles)
        op._var_handles = _ReplaceSplitVarsHandles(self._symbol_mapping).visit(
            op._var_handles
        )
        op._var_types = {
            new_handle.name: op._var_types.get(
                new_handle.name, op._var_types[previous_handle.name]
            )
            for previous_handle, new_handle in zip(
                previous_var_handles, op._var_handles
            )
        }
        return op


class ModelRenamer:
    def rewrite(self, subject: AST_NODE, symbol_mapping: SymbolRenaming) -> AST_NODE:
        if len(symbol_mapping) == 0:
            return subject
        subject = _ReplaceSplitVarsHandles(symbol_mapping).visit(subject)
        subject = _ReplaceSplitVarsExpressions(symbol_mapping).visit(subject)
        return subject
