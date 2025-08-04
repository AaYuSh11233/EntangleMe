import ast
from typing import Any, cast

import sympy

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.model.handle_binding import HandleBinding

from classiq.evaluators.qmod_annotated_expression import (
    QmodAnnotatedExpression,
    QmodExprNodeId,
)
from classiq.evaluators.qmod_expression_visitors.out_of_place_node_transformer import (
    OutOfPlaceNodeTransformer,
)
from classiq.evaluators.qmod_expression_visitors.sympy_wrappers import (
    BitwiseAnd,
    BitwiseNot,
    BitwiseOr,
    BitwiseXor,
    LShift,
    RShift,
)
from classiq.model_expansions.atomic_expression_functions_defs import do_div

_SYMPY_WRAPPERS = {
    wrapper.__name__: wrapper
    for wrapper in [
        BitwiseAnd,
        BitwiseNot,
        BitwiseOr,
        BitwiseXor,
        LShift,
        RShift,
    ]
} | {
    do_div.__name__: do_div,
}


class _VarMaskTransformer(OutOfPlaceNodeTransformer):
    def __init__(self, expr_val: QmodAnnotatedExpression) -> None:
        self._expr_val = expr_val
        self._mask_id = 0
        self.masks: dict[str, QmodExprNodeId] = {}
        self._assigned_masks: dict[HandleBinding, str] = {}

    def _create_mask(self) -> str:
        mask = f"x{self._mask_id}"
        self._mask_id += 1
        return mask

    def visit(self, node: ast.AST) -> ast.AST:
        if self._expr_val.has_value(node):
            return ast.parse(str(self._expr_val.get_value(node)))
        if self._expr_val.has_var(node):
            var = self._expr_val.get_var(node)
            if var in self._assigned_masks:
                mask = self._assigned_masks[var]
            else:
                mask = self._create_mask()
                self._assigned_masks[var] = mask
                self.masks[mask] = id(node)
            return ast.Name(id=mask)
        if self._expr_val.has_quantum_subscript(node):
            mask = self._create_mask()
            self.masks[mask] = id(node)
            return ast.Name(id=mask)
        return super().visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        mask = self._create_mask()
        self.masks[mask] = id(node)
        return ast.Name(id=mask)


class _InverseVarMaskTransformer(OutOfPlaceNodeTransformer):
    def __init__(
        self, expr_val: QmodAnnotatedExpression, masks: dict[str, QmodExprNodeId]
    ) -> None:
        self._expr_val = expr_val
        self._masks = masks

    def visit_Name(self, node: ast.Name) -> Any:
        name = node.id
        if name in self._masks:
            mask_id = self._masks[name]
            if not self._expr_val.has_node(mask_id):
                raise ClassiqInternalExpansionError
            return ast.Name(id=ast.unparse(self._expr_val.get_node(mask_id)))
        return node


class _SympyCompatibilityTransformer(OutOfPlaceNodeTransformer):
    def visit_BoolOp(self, node: ast.BoolOp) -> ast.Call:
        if len(node.values) != 2:
            raise ClassiqInternalExpansionError
        node = cast(ast.BoolOp, self.generic_visit(node))
        if isinstance(node.op, ast.Or):
            sympy_func = "Or"
        else:
            sympy_func = "And"
        return ast.Call(func=ast.Name(id=sympy_func), args=node.values, keywords=[])

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        node = cast(ast.UnaryOp, self.generic_visit(node))
        if isinstance(node.op, ast.Not):
            sympy_func = "Not"
        elif isinstance(node.op, ast.Invert):
            sympy_func = BitwiseNot.__name__
        else:
            return node
        return ast.Call(func=ast.Name(id=sympy_func), args=[node.operand], keywords=[])

    def visit_Compare(self, node: ast.Compare) -> ast.Call:
        if len(node.ops) != 1:
            raise ClassiqInternalExpansionError
        node = cast(ast.Compare, self.generic_visit(node))
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            sympy_func = "Eq"
        elif isinstance(op, ast.NotEq):
            sympy_func = "Ne"
        elif isinstance(op, ast.Lt):
            sympy_func = "Lt"
        elif isinstance(op, ast.LtE):
            sympy_func = "Le"
        elif isinstance(op, ast.Gt):
            sympy_func = "Gt"
        elif isinstance(op, ast.GtE):
            sympy_func = "Ge"
        else:
            raise ClassiqInternalExpansionError
        return ast.Call(
            func=ast.Name(id=sympy_func),
            args=[node.left, node.comparators[0]],
            keywords=[],
        )

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        node = cast(ast.BinOp, self.generic_visit(node))
        if isinstance(node.op, ast.LShift):
            sympy_func = LShift.__name__
        elif isinstance(node.op, ast.RShift):
            sympy_func = RShift.__name__
        elif isinstance(node.op, ast.BitOr):
            sympy_func = BitwiseOr.__name__
        elif isinstance(node.op, ast.BitXor):
            sympy_func = BitwiseXor.__name__
        elif isinstance(node.op, ast.BitAnd):
            sympy_func = BitwiseAnd.__name__
        elif isinstance(node.op, ast.Div):
            return ast.Call(
                func=ast.Name(id=do_div.__name__),
                args=[node.left, node.right],
                keywords=[],
            )
        else:
            return node
        return ast.Call(
            func=ast.Name(id=sympy_func), args=[node.left, node.right], keywords=[]
        )


class _InverseSympyCompatibilityTransformer(OutOfPlaceNodeTransformer):
    def visit_Call(self, node: ast.Call) -> Any:
        node = cast(ast.Call, self.generic_visit(node))
        if not isinstance(node.func, ast.Name):
            raise ClassiqInternalExpansionError
        func = node.func.id

        if (
            func
            in {
                "Eq",
                "Ne",
                "Lt",
                "Le",
                "Gt",
                "Ge",
                LShift.__name__,
                RShift.__name__,
                BitwiseOr.__name__,
                BitwiseXor.__name__,
                BitwiseAnd.__name__,
            }
            and (len(node.args) != 2 or len(node.keywords) > 0)
        ) or (
            func in {BitwiseNot.__name__}
            and (len(node.args) != 1 or len(node.keywords) > 0)
        ):
            raise ClassiqInternalExpansionError

        if func == BitwiseNot.__name__:
            return ast.UnaryOp(op=ast.Invert(), operand=node.args[0])

        if func == "Eq":
            return ast.Compare(
                left=node.args[0], ops=[ast.Eq()], comparators=[node.args[1]]
            )
        if func == "Ne":
            return ast.Compare(
                left=node.args[0], ops=[ast.NotEq()], comparators=[node.args[1]]
            )
        if func == "Lt":
            return ast.Compare(
                left=node.args[0], ops=[ast.Lt()], comparators=[node.args[1]]
            )
        if func == "Le":
            return ast.Compare(
                left=node.args[0], ops=[ast.LtE()], comparators=[node.args[1]]
            )
        if func == "Gt":
            return ast.Compare(
                left=node.args[0], ops=[ast.Gt()], comparators=[node.args[1]]
            )
        if func == "GtE":
            return ast.Compare(
                left=node.args[0], ops=[ast.GtE()], comparators=[node.args[1]]
            )

        if func == LShift.__name__:
            return ast.BinOp(left=node.args[0], op=ast.LShift(), right=node.args[1])
        if func == RShift.__name__:
            return ast.BinOp(left=node.args[0], op=ast.RShift(), right=node.args[1])
        if func == BitwiseOr.__name__:
            return ast.BinOp(left=node.args[0], op=ast.BitOr(), right=node.args[1])
        if func == BitwiseXor.__name__:
            return ast.BinOp(left=node.args[0], op=ast.BitXor(), right=node.args[1])
        if func == BitwiseAnd.__name__:
            return ast.BinOp(left=node.args[0], op=ast.BitAnd(), right=node.args[1])

        if func == "Mod":
            return ast.BinOp(left=node.args[0], op=ast.Mod(), right=node.args[1])
        if func == "Max":
            node.func.id = "max"
        elif func == "Min":
            node.func.id = "min"

        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        node = cast(ast.UnaryOp, self.generic_visit(node))

        if isinstance(node.op, ast.Invert):
            return ast.UnaryOp(op=ast.Not(), operand=node.operand)

        return node

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        node = cast(ast.BinOp, self.generic_visit(node))

        if isinstance(node.op, ast.BitOr):
            return ast.BoolOp(op=ast.Or(), values=[node.left, node.right])
        if isinstance(node.op, ast.BitAnd):
            return ast.BoolOp(op=ast.And(), values=[node.left, node.right])

        return node


def simplify_qmod_expression(expr_val: QmodAnnotatedExpression) -> str:
    if expr_val.has_value(expr_val.root):
        raise ClassiqInternalExpansionError(
            "This expression is a constant value. No need for simplification"
        )
    var_mask_transformer = _VarMaskTransformer(expr_val)
    mask_expr = var_mask_transformer.visit(expr_val.root)
    sympy_expr = _SympyCompatibilityTransformer().visit(mask_expr)
    simplified_expr = str(
        sympy.sympify(ast.unparse(sympy_expr), locals=_SYMPY_WRAPPERS)
    )
    restored_expr = _InverseSympyCompatibilityTransformer().visit(
        ast.parse(simplified_expr, mode="eval")
    )
    restored_expr = _InverseVarMaskTransformer(
        expr_val, var_mask_transformer.masks
    ).visit(restored_expr)
    return ast.unparse(restored_expr)
