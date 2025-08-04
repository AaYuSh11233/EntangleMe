import ast
import copy
from typing import TYPE_CHECKING, Union

from classiq.interface.exceptions import ClassiqInternalExpansionError

from classiq.evaluators.qmod_expression_visitors.sympy_wrappers import LogicalXor


class BooleanExpressionOptimizer(ast.NodeTransformer):
    """
    This class assumes that all variables in the expression are single qubit.
    It does the following:
    It checks whether the expression can be transformed into a boolean expression with boolean
    variables (i.e, single-qubit variables), and if so, does the transformation by converting bitwise
    ops to their boolean analogs.
    The condition is that the expression consists of bitwise operations and relational operations only,
    and not operations like addition.
    The transformation results in better circuits.
    """

    def __init__(self) -> None:
        self._is_convertible: bool = False

    @property
    def is_convertible(self) -> bool:
        return self._is_convertible

    def visit_Expr(self, node: ast.Expr) -> ast.Expr:
        self._is_convertible = False
        original_expr = copy.deepcopy(node)
        self.generic_visit(node)
        return node if self._is_convertible else original_expr

    def visit_operator(self, node: ast.operator) -> ast.operator:
        self._is_convertible = False
        return node

    def visit_BinOp(self, node: ast.BinOp) -> Union[ast.BinOp, ast.BoolOp]:
        self.generic_visit(node)
        self._is_convertible = self._is_bool(node)
        if not self._is_convertible:
            return node

        return self.visit(self._convert_bin_op_to_bool_op(node))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        self.generic_visit(node)
        self._is_convertible = self._is_bool(node)
        if not self._is_convertible:
            return node

        return ast.UnaryOp(op=ast.Not(), operand=node.operand)

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise ClassiqInternalExpansionError

        self.generic_visit(node)
        self._is_convertible = self._is_bool(node)
        if not self._is_convertible:
            return node

        if not (
            isinstance(node.left, ast.Constant)
            or isinstance(node.comparators[0], ast.Constant)
        ):
            return node

        return self._simplify_trivial_equality(node)

    def visit_Call(self, node: ast.Call) -> ast.Call:
        self._is_convertible = (
            isinstance(node.func, ast.Name) and node.func.id == LogicalXor.__name__
        )
        return node

    def _is_bool(self, node: ast.AST) -> bool:
        if isinstance(node, (ast.BoolOp, ast.Name)):  # Name due to boolean vars
            return True
        if isinstance(node, ast.BinOp):
            return (
                self._is_bool(node.left)
                and self._is_bool(node.right)
                and isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor))
            )
        if isinstance(node, ast.Constant):
            return isinstance(node.value, int) and node.value in (0, 1)
        if isinstance(node, ast.UnaryOp):
            return isinstance(node.op, (ast.Invert, ast.Not)) and self._is_bool(
                node.operand
            )
        if isinstance(node, ast.Compare):
            return (
                self._is_bool(node.left)
                and self._is_bool(node.comparators[0])
                and isinstance(node.ops[0], (ast.Eq, ast.NotEq))
            )
        if isinstance(node, ast.Call):
            return (
                isinstance(node.func, ast.Name) and node.func.id == LogicalXor.__name__
            )
        return False

    def _convert_bin_op_to_bool_op(self, node: ast.BinOp) -> ast.AST:
        if isinstance(node.op, ast.BitOr):
            return ast.BoolOp(op=ast.Or(), values=[node.left, node.right])
        if isinstance(node.op, ast.BitAnd):
            return ast.BoolOp(op=ast.And(), values=[node.left, node.right])
        if isinstance(node.op, ast.BitXor):
            return self._simplify_xor(node)
        raise ClassiqInternalExpansionError

    @staticmethod
    def _simplify_xor(node: ast.BinOp) -> ast.AST:
        if not (
            isinstance(node.left, ast.Constant) or isinstance(node.right, ast.Constant)
        ):
            return ast.Call(
                func=ast.Name(LogicalXor.__name__),
                args=[node.left, node.right],
                keywords=[],
            )

        if isinstance(node.left, ast.Constant):
            constant = node.left.value
            other = node.right
        else:
            if TYPE_CHECKING:
                assert isinstance(node.right, ast.Constant)
            try:
                constant = node.right.value
            except AttributeError as e:
                raise e
            other = node.left

        return other if constant == 0 else ast.UnaryOp(op=ast.Not(), operand=other)

    @staticmethod
    def _simplify_trivial_equality(node: ast.Compare) -> ast.AST:
        if isinstance(node.left, ast.Constant):
            val = node.left.value
            other = node.comparators[0]
        else:
            if TYPE_CHECKING:
                assert isinstance(node.comparators[0], ast.Constant)
            val = node.comparators[0].value
            other = node.left

        to_invert = (val == 0 and isinstance(node.ops[0], ast.Eq)) or (
            val == 1 and isinstance(node.ops[0], ast.NotEq)
        )

        return ast.UnaryOp(op=ast.Not(), operand=other) if to_invert else other


class BooleanExpressionFuncLibAdapter(ast.NodeTransformer):
    """
    The class assumes that the expression result is single-qubit.

    Due to limitations on the inplace arithmetic in our function library, this visitor checks whether
    the expression has one of the following forms:
    a. A single, simple boolean assignment (res ^= x).
    b. A bitwise-not operation on a boolean expression (res ^= ~(x > 5)).
    The former will be transformed into res ^= (x == 1). The latter to (res ^= x > 5) and then the Interpreter
    will append an X gate to the result variable.
    To understand the necessity of this transformation, see the _OPERATIONS_ALLOWING_TARGET variable
    which limits the possible inplace operations. Not is forbidden, and a simple assignment res ^= x
    is converted into an addition res ^= x + 0, which is also forbidden.

    """

    def __init__(self, is_boolean_optimized: bool) -> None:
        self._to_invert: bool = False
        self._is_boolean_optimized = is_boolean_optimized

    @property
    def to_invert(self) -> bool:
        return self._to_invert

    def visit_Expr(self, node: ast.Expr) -> ast.Expr:
        self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            node.value = ast.Compare(
                left=node.value,
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=1)],
            )
        if isinstance(node.value, ast.UnaryOp) and isinstance(
            node.value.op, (ast.Not, ast.Invert)
        ):
            self._to_invert = not self._to_invert
            node.value = node.value.operand
            return self.visit(node)

        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.UnaryOp:
        """Due to Sympy crap, we need to translate the Invert nodes to Not"""
        if not (self._is_boolean_optimized and isinstance(node.op, ast.Invert)):
            return node
        self.generic_visit(node)
        return ast.UnaryOp(op=ast.Not(), operand=node.operand)

    def visit_BinOp(self, node: ast.BinOp) -> Union[ast.BinOp, ast.Call]:
        """Due to Sympy crap, we need to translate the Xor nodes to our LogicalXor"""
        if not (self._is_boolean_optimized and isinstance(node.op, ast.BitXor)):
            return node
        self.generic_visit(node)
        return ast.Call(
            func=ast.Name(LogicalXor.__name__),
            args=[node.left, node.right],
            keywords=[],
        )
