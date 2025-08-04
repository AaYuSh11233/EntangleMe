import ast
from typing import TYPE_CHECKING, cast

from classiq.interface.exceptions import ClassiqExpansionError

MISSING_SLICE_VALUE_PLACEHOLDER = "MISSING_SLICE_VALUE"


def translate_to_sympy(expr: str) -> str:
    node = ast.parse(expr)
    node = ExpressionSympyTranslator().visit(node)
    # node is a Module, we want an Expression
    if TYPE_CHECKING:
        assert isinstance(node.body[0], ast.Expr)
    expression = ast.Expression(node.body[0].value)

    return ast.unparse(ast.fix_missing_locations(expression))


class ExpressionSympyTranslator(ast.NodeTransformer):
    BINARY_OPERATORS: dict[type[ast.AST], str] = {
        ast.BitOr: "BitwiseOr",
        ast.BitAnd: "BitwiseAnd",
        ast.BitXor: "BitwiseXor",
        ast.Div: "do_div",
        ast.RShift: "RShift",
        ast.LShift: "LShift",
    }

    UNARY_OPERATORS: dict[type[ast.AST], str] = {
        ast.Invert: "BitwiseNot",
        ast.Not: "Not",
    }

    BOOLEAN_OPERATORS: dict[type[ast.AST], str] = {
        ast.Or: "Or",
        ast.And: "And",
    }

    COMPARE_OPERATORS: dict[type[ast.AST], str] = {
        ast.Eq: "Eq",
        ast.NotEq: "Ne",
    }

    SPECIAL_FUNCTIONS: dict[str, str] = {
        "max": "Max",
        "min": "Min",
    }

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        sympy_class = self.BINARY_OPERATORS.get(node.op.__class__)
        if sympy_class is not None:
            left = self.visit(node.left)
            right = self.visit(node.right)

            new_node = ast.Call(
                func=ast.Name(id=sympy_class, ctx=ast.Load()),
                args=[left, right],
                starargs=None,
                keywords=[],
                kwargs=None,
            )

            return new_node
        return self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if len(node.ops) > 1:
            raise ClassiqExpansionError(
                f"Qmod expressions do not support chained comparison, as done in {ast.unparse(node)}"
            )
        sympy_class = self.COMPARE_OPERATORS.get(node.ops[0].__class__)
        if sympy_class is not None:
            left = self.visit(node.left)
            right = self.visit(node.comparators[0])

            new_node = ast.Call(
                func=ast.Name(id=sympy_class, ctx=ast.Load()),
                args=[left, right],
                starargs=None,
                keywords=[],
                kwargs=None,
            )

            return new_node
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        sympy_class = self.BOOLEAN_OPERATORS.get(node.op.__class__)
        if sympy_class is not None:
            values = [self.visit(value) for value in node.values]

            new_node = ast.Call(
                func=ast.Name(id=sympy_class, ctx=ast.Load()),
                args=values,
                starargs=None,
                keywords=[],
                kwargs=None,
            )

            return new_node
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        sympy_class = self.UNARY_OPERATORS.get(node.op.__class__)
        if sympy_class is not None:
            operand = self.visit(node.operand)

            new_node = ast.Call(
                func=ast.Name(id=sympy_class, ctx=ast.Load()),
                args=[operand],
                starargs=None,
                keywords=[],
                kwargs=None,
            )

            return new_node
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if isinstance(node.func, ast.Name) and node.func.id == "Piecewise":
            return self._visit_piecewise(node)

        if (
            not isinstance(node.func, ast.Name)
            or node.func.id not in self.SPECIAL_FUNCTIONS
        ):
            return self.generic_visit(node)

        return ast.Call(
            func=ast.Name(self.SPECIAL_FUNCTIONS[node.func.id]),
            args=[self.visit(arg) for arg in (node.args)],
            keywords=[self.visit(arg) for arg in node.keywords],
        )

    def _visit_piecewise(self, node: ast.Call) -> ast.AST:
        # sympy Piecewise expression may include bitwise operations:
        # Piecewise((0, Eq(x, 0)), (0.5, Eq(x, 1) | Eq(x, 2)), (1, True))
        #                                         ^
        # We should avoid converting these to 'BitwiseOr' and such.
        return ast.Call(
            func=node.func,
            args=[
                ast.Tuple(
                    elts=(
                        self.generic_visit(cast(ast.Tuple, arg).elts[0]),
                        cast(ast.Tuple, arg).elts[1],
                    )
                )
                for arg in node.args
            ],
            keywords=node.keywords,
        )

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        if isinstance(node.slice, ast.Slice):
            if node.slice.lower is not None:
                lower = self.visit(node.slice.lower)
            else:
                lower = ast.Name(MISSING_SLICE_VALUE_PLACEHOLDER)
            if node.slice.upper is not None:
                upper = self.visit(node.slice.upper)
            else:
                upper = ast.Name(MISSING_SLICE_VALUE_PLACEHOLDER)
            return ast.Call(
                func=ast.Name("do_slice"),
                args=[self.visit(node.value), lower, upper],
                keywords=[],
            )
        return ast.Call(
            func=ast.Name("do_subscript"),
            args=[self.visit(node.value), self.visit(node.slice)],
            keywords=[],
        )

    def visit_Attribute(self, node: ast.Attribute) -> ast.Call:
        return ast.Call(
            func=ast.Name("get_field"),
            args=[self.visit(node.value), ast.Constant(value=node.attr)],
            keywords=[],
        )
