import ast
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable

import numpy as np

from classiq.interface.constants import DEFAULT_DECIMAL_PRECISION

import classiq

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


@dataclass
class ASTToQMODCode(ast.NodeVisitor):
    level: int
    imports: dict[str, int]
    symbolic_imports: dict[str, int]
    decimal_precision: int
    one_line: bool
    indent_seq: str = "    "

    @property
    def indent(self) -> str:
        return self.level * self.indent_seq

    def _handle_imports(self, name: str, is_possibly_symbolic: bool = False) -> None:
        if name in dir(classiq):
            self.imports[name] = 1
        if is_possibly_symbolic and name in dir(classiq.qmod.symbolic):
            self.symbolic_imports[name] = 1

    def visit(self, node: ast.AST) -> str:
        res = super().visit(node)
        if not isinstance(res, str):
            raise AssertionError("Error parsing expression: unsupported AST node.")
        return res

    def visit_Module(self, node: ast.Module) -> str:
        return self.indent.join(self.visit(child) for child in node.body)

    def visit_Attribute(self, node: ast.Attribute) -> str:
        return f"{self.visit(node.value)}.{node.attr}"

    def visit_Name(self, node: ast.Name) -> str:
        self._handle_imports(node.id, True)
        return node.id

    def visit_Num(self, node: ast.Num) -> str:
        return str(np.round(node.n, self.decimal_precision))

    def visit_Str(self, node: ast.Str) -> str:
        return repr(node.s)

    def visit_Constant(self, node: ast.Constant) -> str:
        return repr(node.value)

    def visit_BinOp(self, node: ast.BinOp) -> str:
        return "({} {} {})".format(
            self.visit(node.left),
            BINARY_OPS[type(node.op)],
            self.visit(node.right),
        )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        unary_op = UNARY_OPS[type(node.op)]
        space = " " if unary_op == "not" else ""
        return f"({unary_op}{space}{self.visit(node.operand)})"

    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        return "({})".format(
            (" " + BOOL_OPS[type(node.op)] + " ").join(
                self.visit(value) for value in node.values
            )
        )

    def visit_Compare(self, node: ast.Compare) -> str:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise AssertionError("Error parsing comparison expression.")
        return "({} {} {})".format(
            self.visit(node.left),
            COMPARE_OPS[type(node.ops[0])],
            self.visit(node.comparators[0]),
        )

    def visit_List(self, node: ast.List) -> str:
        elts = node.elts
        elements = self.indent_items(lambda: [self.visit(element) for element in elts])
        return f"[{elements}]"

    def visit_Subscript(self, node: ast.Subscript) -> str:
        return f"{self.visit(node.value)}[{_remove_redundant_parentheses(self.visit(node.slice))}]"

    def visit_Slice(self, node: ast.Slice) -> str:
        if node.lower is None or node.upper is None or node.step is not None:
            raise AssertionError("Error parsing slice expression.")
        return f"{self.visit(node.lower)}:{self.visit(node.upper)}"

    def visit_Call(self, node: ast.Call) -> str:
        func = self.visit(node.func)
        self._handle_imports(func, True)
        if func == "get_field":
            if len(node.args) != 2:
                raise AssertionError("Error parsing struct field access.")
            field = str(self.visit(node.args[1])).replace("'", "")
            if not IDENTIFIER.match(field):
                raise AssertionError("Error parsing struct field access.")
            return f"{self.visit(node.args[0])}.{field}"
        elif func == "do_subscript":
            if len(node.args) != 2:
                raise AssertionError("Error parsing array subscript.")
            return f"{self.visit(node.args[0])}[{self.visit(node.args[1])}]"
        elif func == "struct_literal":
            if len(node.args) != 1 or not isinstance(node.args[0], ast.Name):
                raise AssertionError("Error parsing struct literal.")
            keywords = node.keywords
            initializer_list = self.indent_items(
                lambda: [
                    f"{keyword.arg} = {self._cleaned_ast_to_code(keyword.value)}"
                    for keyword in keywords
                    if keyword.arg is not None
                ]
            )
            return f"{self.visit(node.args[0])}({initializer_list})"
        else:
            args = [self._cleaned_ast_to_code(arg) for arg in node.args]
            kwargs = [
                f"{kwarg.arg}={self._cleaned_ast_to_code(kwarg.value)}"
                for kwarg in node.keywords
            ]
            return "{}({})".format(func, ", ".join(args + kwargs))

    def visit_Expr(self, node: ast.Expr) -> str:
        return self._cleaned_ast_to_code(node.value)

    def generic_visit(self, node: ast.AST) -> None:
        raise AssertionError("Cannot parse node of type: " + type(node).__name__)

    def indent_items(self, items: Callable[[], list[str]]) -> str:
        should_indent = not self.one_line and (
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
        return _remove_redundant_parentheses(self.visit(node))


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
    imports: dict[str, int],
    symbolic_imports: dict[str, int],
    level: int = 0,
    decimal_precision: int = DEFAULT_DECIMAL_PRECISION,
    one_line: bool = False,
) -> str:
    return ASTToQMODCode(
        level=level,
        decimal_precision=decimal_precision,
        imports=imports,
        one_line=one_line,
        symbolic_imports=symbolic_imports,
    ).visit(ast.parse(expr))
