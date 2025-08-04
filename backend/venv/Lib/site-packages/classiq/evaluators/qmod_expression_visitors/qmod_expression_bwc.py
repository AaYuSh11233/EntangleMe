import ast
from typing import Any, cast

import sympy

MAX_PIECEWISE_LOOPS = 1000


# FIXME: Remove with deprecation (CLS-3214)
class QmodExpressionBwc(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> Any:
        node = cast(ast.Call, self.generic_visit(node))
        if not isinstance(node.func, ast.Name):
            return node
        func = node.func.id
        args = node.args
        kwargs = node.keywords
        num_args = len(args)
        num_kwargs = len(kwargs)

        if func == "BitwiseNot":
            if num_args != 1 or num_kwargs != 0:
                return node
            return ast.UnaryOp(op=ast.Invert(), operand=args[0])
        if func == "LShift":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.LShift(), right=args[1])
        if func == "RShift":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.RShift(), right=args[1])
        if func == "BitwiseOr":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.BitOr(), right=args[1])
        if func == "BitwiseXor":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.BitXor(), right=args[1])
        if func == "BitwiseAnd":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.BitAnd(), right=args[1])

        if func == "LogicalXor":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.BinOp(left=args[0], op=ast.BitXor(), right=args[1])

        if func == "Eq":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.Eq()], comparators=[args[1]])
        if func == "Ne":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.NotEq()], comparators=[args[1]])
        if func == "Lt":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.Lt()], comparators=[args[1]])
        if func == "Le":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.LtE()], comparators=[args[1]])
        if func == "Gt":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.Gt()], comparators=[args[1]])
        if func == "Ge":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Compare(left=args[0], ops=[ast.GtE()], comparators=[args[1]])

        if func == "struct_literal":
            if num_args != 1:
                return node
            return ast.Call(func=node.args[0], args=[], keywords=node.keywords)

        if func == "do_subscript":
            if num_args != 2 or num_kwargs != 0:
                return node
            return ast.Subscript(value=args[0], slice=args[1])

        if func == "get_field":
            if num_args != 2 or num_kwargs != 0:
                return node
            attr = args[1]
            if not isinstance(attr, ast.Constant):
                return node
            return ast.Attribute(value=args[0], attr=attr.value)

        if func == "Piecewise":
            if num_args == 0:
                return node
            first_piece = args[0]
            if not isinstance(first_piece, ast.Tuple) or len(first_piece.elts) != 2:
                return node
            first_cond = first_piece.elts[1]
            if isinstance(first_cond, ast.BinOp):
                first_cond = first_cond.right
            if not isinstance(first_cond, ast.Compare) or len(first_cond.ops) != 1:
                return node
            index_var_node = first_cond.left
            if not isinstance(index_var_node, ast.Name):
                return node
            index_var = index_var_node.id
            last_cond = args[-1]
            if not isinstance(last_cond, ast.Tuple) or len(last_cond.elts) != 2:
                return node
            last_value = last_cond.elts[0]
            if not isinstance(last_value, ast.Constant) and (
                not isinstance(last_value, ast.UnaryOp)
                or not isinstance(last_value.operand, ast.Constant)
            ):
                return node
            dummy_var_name = f"{index_var}_not_it"
            last_cond.elts[0] = ast.Name(id=dummy_var_name)
            items: list = []
            idx = 0
            for idx in range(MAX_PIECEWISE_LOOPS):
                item = sympy.sympify(ast.unparse(node), locals={index_var: idx})
                if str(item) == dummy_var_name:
                    items.append(last_value)
                    break
                items.append(ast.parse(str(item), mode="eval").body)
            if idx == MAX_PIECEWISE_LOOPS:
                return node
            return ast.Subscript(
                value=ast.List(elts=items), slice=ast.Name(id=index_var)
            )

        return node
