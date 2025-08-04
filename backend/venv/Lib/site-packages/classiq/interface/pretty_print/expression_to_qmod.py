import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from classiq.interface.constants import DEFAULT_DECIMAL_PRECISION

IDENTIFIER = re.compile(r"[a-zA-Z_]\w*")
BINARY_OPS: Mapping[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.LShift: "<<",
    ast.RShift: ">>",
}
BOOL_OPS: Mapping[type[ast.boolop], str] = {ast.And: "and", ast.Or: "or"}
UNARY_OPS: Mapping[type[ast.unaryop], str] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Invert: "~",
    ast.Not: "not",
}
COMPARE_OPS: Mapping[type[ast.cmpop], str] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}
LIST_FORMAT_CHAR_LIMIT = 20


class PrettyPrinterError(AssertionError):
    pass


@dataclass
class ASTToQMODCode:
    level: int
    decimal_precision: Optional[int]
    indent_seq: str = "  "

    @property
    def indent(self) -> str:
        return self.level * self.indent_seq

    def visit(self, node: ast.AST) -> str:
        return self.ast_to_code(node)

    def ast_to_code(self, node: ast.AST) -> str:
        if isinstance(node, ast.Module):
            return self.indent.join(self.ast_to_code(child) for child in node.body)
        elif isinstance(node, ast.Attribute):
            # FIXME: identify enum member accesses by type name (CLS-2858)
            if (
                isinstance(node.value, ast.Name)
                and len(node.value.id) > 0
                and node.value.id[0].isupper()
            ):
                return f"{node.value.id}::{node.attr}"
            return f"{self.visit(node.value)}.{node.attr}"
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Num):
            if self.decimal_precision is None:
                return str(node.n)
            return str(np.round(node.n, self.decimal_precision))
        elif isinstance(node, ast.Str):
            return repr(node.s)
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.BinOp):
            return "({} {} {})".format(
                self.ast_to_code(node.left),
                BINARY_OPS[type(node.op)],
                self.ast_to_code(node.right),
            )
        elif isinstance(node, ast.UnaryOp):
            unary_op = UNARY_OPS[type(node.op)]
            space = " " if unary_op == "not" else ""
            return f"({unary_op}{space}{self.ast_to_code(node.operand)})"
        elif isinstance(node, ast.BoolOp):
            return "({})".format(
                (" " + BOOL_OPS[type(node.op)] + " ").join(
                    self.ast_to_code(value) for value in node.values
                )
            )
        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise PrettyPrinterError("Error parsing comparison expression.")
            return "({} {} {})".format(
                self.ast_to_code(node.left),
                COMPARE_OPS[type(node.ops[0])],
                self.ast_to_code(node.comparators[0]),
            )
        elif isinstance(node, ast.List):
            elts = node.elts
            elements = self.indent_items(
                lambda: [self.ast_to_code(element) for element in elts]
            )
            return f"[{elements}]"
        elif isinstance(node, ast.Subscript):
            return f"{self.ast_to_code(node.value)}[{_remove_redundant_parentheses(self.ast_to_code(node.slice))}]"
        elif isinstance(node, ast.Slice):
            # A QMOD expression does not support slice step
            if node.lower is None or node.upper is None or node.step is not None:
                raise PrettyPrinterError("Error parsing slice expression.")
            return f"{self.ast_to_code(node.lower)}:{self.ast_to_code(node.upper)}"
        elif isinstance(node, ast.Call):
            func = self.ast_to_code(node.func)
            if func == "get_field":
                if len(node.args) != 2:
                    raise PrettyPrinterError("Error parsing struct field access.")
                field = str(self.ast_to_code(node.args[1])).replace("'", "")
                if not IDENTIFIER.match(field):
                    raise PrettyPrinterError("Error parsing struct field access.")
                return f"{self.ast_to_code(node.args[0])}.{field}"
            elif func == "struct_literal":
                if len(node.args) != 1 or not isinstance(node.args[0], ast.Name):
                    raise PrettyPrinterError("Error parsing struct literal.")
                keywords = node.keywords
                initializer_list = self.indent_items(
                    lambda: [
                        f"{keyword.arg}={self._cleaned_ast_to_code(keyword.value)}"
                        for keyword in keywords
                        if keyword.arg is not None
                    ]
                )
                return f"{self.ast_to_code(node.args[0])} {{{initializer_list}}}"
            elif func == "do_subscript":
                if len(node.args) != 2:
                    raise PrettyPrinterError("Error parsing array access.")
                return f"{self.ast_to_code(node.args[0])}[{self.ast_to_code(node.args[1])}]"
            elif len(node.keywords) > 0:
                # struct instance
                keywords = node.keywords
                initializer_list = self.indent_items(
                    lambda: [
                        f"{keyword.arg}={self._cleaned_ast_to_code(keyword.value)}"
                        for keyword in keywords
                        if keyword.arg is not None
                    ]
                )
                return f"{func} {{{initializer_list}}}"
            else:
                args = [self._cleaned_ast_to_code(arg) for arg in node.args]
                kwargs = [
                    f"{kwarg.arg}={self._cleaned_ast_to_code(kwarg.value)}"
                    for kwarg in node.keywords
                ]
                return "{}({})".format(func, ", ".join(args + kwargs))
        elif isinstance(node, ast.Expr):
            return self._cleaned_ast_to_code(node.value)
        else:
            raise PrettyPrinterError("Error parsing expression: unsupported AST node.")

    def indent_items(self, items: Callable[[], list[str]]) -> str:
        should_indent = (
            len("".join([i.strip() for i in items()])) >= LIST_FORMAT_CHAR_LIMIT
        )
        if should_indent:
            self.level += 1
            left_ws = "\n" + self.indent
            inner_ws = ",\n" + self.indent
        else:
            left_ws = ""
            inner_ws = ", "
        items_ = items()
        if should_indent:
            self.level -= 1
            right_ws = "\n" + self.indent
        else:
            right_ws = ""
        return f"{left_ws}{inner_ws.join(items_)}{right_ws}"

    def _cleaned_ast_to_code(self, node: ast.AST) -> str:
        return _remove_redundant_parentheses(self.ast_to_code(node))


def _remove_redundant_parentheses(expr: str) -> str:
    if not (expr.startswith("(") and expr.endswith(")")):
        return expr
    parentheses_map: dict[int, int] = dict()
    stack: list[int] = []
    for index, char in enumerate(expr):
        if char == "(":
            stack.append(index)
        elif char == ")":
            parentheses_map[stack.pop()] = index
    index = 0
    original_length = len(expr)
    while (
        index in parentheses_map
        and parentheses_map[index] == original_length - index - 1
    ):
        expr = expr[1:-1]
        index += 1
    return expr


def transform_expression(
    expr: str,
    level: int = 0,
    decimal_precision: Optional[int] = DEFAULT_DECIMAL_PRECISION,
) -> str:
    return ASTToQMODCode(level=level, decimal_precision=decimal_precision).visit(
        ast.parse(expr)
    )
