import ast
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional, Union

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.arith.arithmetic_expression_validator import (
    DEFAULT_SUPPORTED_FUNC_NAMES,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.sympy_supported_expressions import (
    SYMPY_SUPPORTED_EXPRESSIONS,
)
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)


class VarRefCollector(ast.NodeVisitor):
    def __init__(
        self,
        ignore_duplicated_handles: bool = False,
        unevaluated: bool = False,
        ignore_sympy_symbols: bool = False,
    ) -> None:
        self._var_handles: dict[HandleBinding, bool] = {}
        self._ignore_duplicated_handles = ignore_duplicated_handles
        self._ignore_sympy_symbols = ignore_sympy_symbols
        self._unevaluated = unevaluated
        self._is_nested = False
        self._in_subscript = False

    @property
    def var_handles(self) -> list[HandleBinding]:
        return list(self._var_handles)

    @property
    def subscript_handles(self) -> list[HandleBinding]:
        return [
            handle for handle, in_subscript in self._var_handles.items() if in_subscript
        ]

    def visit(self, node: ast.AST) -> Union[
        SubscriptHandleBinding,
        SlicedHandleBinding,
        FieldHandleBinding,
        HandleBinding,
        None,
    ]:
        res = super().visit(node)
        if not self._ignore_duplicated_handles and len(self._var_handles) != len(
            {handle.name for handle in self._var_handles}
        ):
            raise ClassiqExpansionError(
                "Multiple non-identical variable references in an expression are not supported."
            )
        return res

    def visit_Subscript(self, node: ast.Subscript) -> Union[HandleBinding, None]:
        return self._get_subscript_handle(node.value, node.slice)

    def visit_Attribute(self, node: ast.Attribute) -> Optional[FieldHandleBinding]:
        return self._get_field_handle(node.value, node.attr)

    def visit_Call(self, node: ast.Call) -> Optional[HandleBinding]:
        if not isinstance(node.func, ast.Name):
            return self.generic_visit(node)
        if node.func.id == "get_field":
            if (
                len(node.args) != 2
                or not isinstance(node.args[1], ast.Constant)
                or not isinstance(node.args[1].value, str)
            ):
                raise ClassiqInternalExpansionError("Unexpected 'get_field' arguments")
            return self._get_field_handle(node.args[0], node.args[1].value)
        if node.func.id == "do_subscript":
            if len(node.args) != 2:
                raise ClassiqInternalExpansionError(
                    "Unexpected 'do_subscript' arguments"
                )
            return self._get_subscript_handle(node.args[0], node.args[1])
        return self.generic_visit(node)

    def _get_field_handle(
        self, subject: ast.expr, field: str
    ) -> Optional[FieldHandleBinding]:
        with self.set_nested():
            base_handle = self.visit(subject)
        if base_handle is None:
            return None
        handle = FieldHandleBinding(
            base_handle=base_handle,
            field=field,
        )
        if not self._is_nested:
            self._add_handle(handle)
        return handle

    def _get_subscript_handle(
        self, subject: ast.expr, subscript: ast.expr
    ) -> Optional[HandleBinding]:
        with self.set_in_subscript():
            self.visit(subscript)
        with self.set_nested():
            base_handle = self.visit(subject)
        if base_handle is None:
            return None
        handle: HandleBinding
        if isinstance(subscript, ast.Slice):
            if not self._unevaluated and (
                not isinstance(subscript.lower, ast.Num)
                or not isinstance(subscript.upper, ast.Num)
            ):
                raise ClassiqInternalExpansionError("Unevaluated slice bounds")
            if subscript.lower is None or subscript.upper is None:
                raise ClassiqInternalExpansionError(
                    f"{str(base_handle)!r} slice must specify both lower and upper bounds"
                )
            handle = SlicedHandleBinding(
                base_handle=base_handle,
                start=Expression(expr=ast.unparse(subscript.lower)),
                end=Expression(expr=ast.unparse(subscript.upper)),
            )
        elif not self._unevaluated and not isinstance(subscript, ast.Num):
            raise ClassiqInternalExpansionError("Unevaluated subscript")
        else:
            handle = SubscriptHandleBinding(
                base_handle=base_handle,
                index=Expression(expr=ast.unparse(subscript)),
            )
        if not self._is_nested:
            self._add_handle(handle)
        return handle

    def visit_Name(self, node: ast.Name) -> Optional[HandleBinding]:
        if not self._ignore_sympy_symbols and node.id in set(
            SYMPY_SUPPORTED_EXPRESSIONS
        ) | set(DEFAULT_SUPPORTED_FUNC_NAMES):
            return None
        handle = HandleBinding(name=node.id)
        if not self._is_nested:
            self._add_handle(handle)
        return handle

    @contextmanager
    def set_nested(self, val: bool = True) -> Iterator[None]:
        previous_is_nested = self._is_nested
        self._is_nested = val
        yield
        self._is_nested = previous_is_nested

    @contextmanager
    def set_in_subscript(self) -> Iterator[None]:
        previous_in_subscript = self._in_subscript
        self._in_subscript = True
        with self.set_nested(False):
            yield
        self._in_subscript = previous_in_subscript

    def _add_handle(self, handle: HandleBinding) -> None:
        if handle not in self._var_handles:
            self._var_handles[handle] = self._in_subscript
            return
        if self._in_subscript and not self._var_handles[handle]:
            self._var_handles[handle] = True


class VarRefTransformer(ast.NodeTransformer):
    def __init__(self, var_mapping: dict[str, str]) -> None:
        self.var_mapping = var_mapping

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.var_mapping:
            node.id = self.var_mapping[node.id]
        return node
