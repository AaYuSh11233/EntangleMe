import ast
import itertools
from collections.abc import Iterator
from typing import Any, Optional, Union, cast

from classiq.interface.exceptions import ClassiqArithmeticError

SEPARATOR: str = "_"
OUTPUT_SIZE: str = "output_size"
NOT_POWER_OF_TWO_ERROR_MSG: str = "Only power of 2 modulo is supported"


def _count_str_gen() -> Iterator[str]:
    for n in itertools.count(0):
        yield SEPARATOR + str(n)


class AstNodeRewrite(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.count_str_gen = _count_str_gen()

    def visit(self, node: ast.AST) -> ast.AST:
        new_node = ast.NodeTransformer.visit(self, node=node)
        new_node.id = self.extract_node_id(new_node)
        return new_node

    def extract_node_id(self, node: ast.AST) -> Optional[Union[str, float]]:
        if hasattr(node, "id"):
            return node.id
        elif hasattr(node, "op"):
            return type(node.op).__name__ + next(self.count_str_gen)
        elif hasattr(node, "func"):
            return self.extract_node_id(node.func)
        elif hasattr(node, "value"):
            return node.value
        elif hasattr(node, "ops"):
            return type(node.ops[0]).__name__ + next(self.count_str_gen)
        return None

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        if hasattr(node, OUTPUT_SIZE):
            node.operand.output_size = node.output_size  # type: ignore[attr-defined]

        node = cast(ast.UnaryOp, self.generic_visit(node))
        if isinstance(node.op, ast.UAdd):
            return node.operand
        elif isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return self.visit(ast.Constant(value=-node.operand.value))
        return node

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if hasattr(node, OUTPUT_SIZE):
            node.left.output_size = node.output_size  # type: ignore[attr-defined]
            node.right.output_size = node.output_size  # type: ignore[attr-defined]

        node = cast(ast.BinOp, self.generic_visit(node))
        if isinstance(node.op, ast.Mod):
            if not isinstance(node.right, ast.Constant) or isinstance(
                node.left, ast.Constant
            ):
                raise ClassiqArithmeticError(
                    "Modulo must be between a variable and a constant"
                )
            value = node.right.value
            is_power_2 = value > 0 and (value & (value - 1) == 0)
            if not is_power_2:
                raise ClassiqArithmeticError(NOT_POWER_OF_TWO_ERROR_MSG)
            if not isinstance(node.left, ast.Name):
                node.left.output_size = node.right.value.bit_length() - 1  # type: ignore[attr-defined]
                return node.left
        return node
