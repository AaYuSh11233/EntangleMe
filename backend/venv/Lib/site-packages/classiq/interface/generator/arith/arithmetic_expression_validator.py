import ast
import re
from _ast import AST
from typing import Any, Optional, Union

from sympy import Expr
from typing_extensions import TypeAlias, get_args

from classiq.interface.exceptions import ClassiqArithmeticError, ClassiqValueError
from classiq.interface.generator.arith.ast_node_rewrite import AstNodeRewrite
from classiq.interface.generator.expressions.sympy_supported_expressions import (
    SYMPY_SUPPORTED_EXPRESSIONS,
)

DEFAULT_SUPPORTED_FUNC_NAMES: set[str] = {"CLShift", "CRShift", "min", "max"}

DEFAULT_EXPRESSION_TYPE = "arithmetic"
IDENITIFIER_REGEX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

ValidKeyValuePairs: TypeAlias = dict[str, set[str]]

SupportedNodesTypes = Union[
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.BitOr,
    ast.BitAnd,
    ast.BitXor,
    ast.Invert,
    ast.Compare,
    ast.Eq,
    ast.Mod,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.USub,
    ast.UAdd,
    ast.Sub,
    ast.Gt,
    ast.GtE,
    ast.Lt,
    ast.LtE,
    ast.NotEq,
    ast.LShift,
    ast.RShift,
    ast.Call,
    ast.Mult,
    ast.Pow,
]

DEFAULT_SUPPORTED_NODE_TYPES = get_args(SupportedNodesTypes)


def is_constant(expr: Union[str, Expr]) -> bool:
    try:
        float(expr)
        return True
    except (ValueError, TypeError):
        return False


def is_variable(expr: str) -> bool:
    return IDENITIFIER_REGEX.fullmatch(expr) is not None


class ExpressionValidator(ast.NodeVisitor):
    def __init__(
        self,
        supported_nodes: tuple[type[AST], ...],
        expression_type: str = DEFAULT_EXPRESSION_TYPE,
        supported_functions: Optional[set[str]] = None,
        mode: str = "eval",
    ) -> None:
        super().__init__()
        self.supported_nodes = supported_nodes
        self._expression_type = expression_type
        self._supported_functions = supported_functions or DEFAULT_SUPPORTED_FUNC_NAMES
        self._mode = mode
        self._ast_obj: Optional[ast.AST] = None

    def validate(self, expression: str) -> None:
        try:
            adjusted_expression = self._get_adjusted_expression(expression)
            ast_expr = ast.parse(adjusted_expression, filename="", mode=self._mode)
        except SyntaxError as e:
            raise ClassiqValueError(f"Failed to parse expression {expression!r}") from e
        try:
            self._ast_obj = self.rewrite_ast(ast_expr)
            self.visit(self._ast_obj)
        except RecursionError as e:
            raise ClassiqValueError(
                f"Failed to parse expression since it is too long: {expression}"
            ) from e

    @staticmethod
    def _get_adjusted_expression(expression: str) -> str:
        # This works around the simplification of the trivial expressions such as a + 0, 1 * a, etc.
        if is_variable(expression) or is_constant(expression):
            return f"0 + {expression}"
        return expression

    @property
    def ast_obj(self) -> ast.AST:
        if not self._ast_obj:
            raise ClassiqArithmeticError("Must call `validate` before getting ast_obj")
        return self._ast_obj

    def _check_repeated_variables(
        self, variables: tuple[Any, Any], expr: ast.AST, error_suffix: str
    ) -> None:
        if (
            isinstance(expr, ast.BinOp)
            and isinstance(expr.op, ast.Pow)
            and ast.Pow not in self.supported_nodes
        ):
            raise ClassiqValueError(
                "Raising to a power (<var> ** <exp>) and multiplying a variable by "
                "itself (<var> * <var>) are not supported"
            )
        if (
            all(isinstance(var, ast.Name) for var in variables)
            and variables[0].id == variables[1].id
        ):
            raise ClassiqValueError(
                f"Expression {ast.unparse(expr)!r} is not supported ({error_suffix})"
            )

    @staticmethod
    def _check_multiple_comparators(node: ast.Compare) -> None:
        if len(node.comparators) > 1:
            raise ClassiqValueError(
                "Arithmetic expression with more than 1 comparator is not supported"
            )

    def generic_visit(self, node: ast.AST) -> None:
        self._validate_node_type(node)
        return super().generic_visit(node)

    def _validate_node_type(self, node: ast.AST) -> None:
        if isinstance(node, self.supported_nodes):
            return
        raise ClassiqValueError(
            f"Invalid {self._expression_type} expression: "
            f"{type(node).__name__} is not supported"
        )

    def validate_Compare(self, node: ast.Compare) -> None:  # noqa: N802
        self._check_repeated_variables(
            (node.left, node.comparators[0]),
            node,
            "both sides of the comparison are identical",
        )
        self._check_multiple_comparators(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self.validate_Compare(node)
        self.generic_visit(node)

    def validate_BinOp(self, node: ast.BinOp) -> None:  # noqa: N802
        self._check_repeated_variables(
            (node.left, node.right), node, "both sides of the operation are identical"
        )

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self.validate_BinOp(node)
        self.generic_visit(node)

    def validate_Call(self, node: ast.Call) -> None:  # noqa: N802
        if len(node.args) >= 2:
            self._check_repeated_variables(
                (node.args[0], node.args[1]),
                node,
                "the first two call arguments are identical",
            )
        node_id = AstNodeRewrite().extract_node_id(node)
        if node_id not in self._supported_functions:
            raise ClassiqValueError(f"{node_id} not in supported functions")

        if node_id in ("CLShift", "CRShift") and (
            len(node.args) != 2 or not isinstance(node.args[1], ast.Constant)
        ):
            raise ClassiqValueError("Cyclic Shift expects 2 arguments (exp, int)")

    def visit_Call(self, node: ast.Call) -> None:
        self.validate_Call(node)
        self.generic_visit(node)

    def validate_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        if not isinstance(node.value, (int, float, complex, str)):
            raise ClassiqValueError(
                f"{type(node.value).__name__} literals are not valid in {self._expression_type} expressions"
            )

    def visit_Constant(self, node: ast.Constant) -> None:
        self.validate_Constant(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.generic_visit(node)

    @classmethod
    def rewrite_ast(cls, expression_ast: AST) -> AST:
        return expression_ast


def validate_expression(
    expression: str,
    *,
    supported_nodes: tuple[type[AST], ...] = DEFAULT_SUPPORTED_NODE_TYPES,
    expression_type: str = DEFAULT_EXPRESSION_TYPE,
    supported_functions: Optional[set[str]] = None,
    mode: str = "eval",
) -> ast.AST:
    supported_functions = supported_functions or set(SYMPY_SUPPORTED_EXPRESSIONS).union(
        DEFAULT_SUPPORTED_FUNC_NAMES
    )
    validator = ExpressionValidator(
        supported_nodes,
        expression_type,
        supported_functions,
        mode,
    )
    validator.validate(expression)
    return validator.ast_obj
