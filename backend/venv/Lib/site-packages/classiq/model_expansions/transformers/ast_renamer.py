import ast

_POSSIBLE_HANDLE_AST_TYPES = (ast.Subscript, ast.Attribute, ast.Name)


class _ASTRenamer(ast.NodeTransformer):
    def __init__(self, sub: dict[str, str]) -> None:
        self._sub = sub

    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, _POSSIBLE_HANDLE_AST_TYPES):
            node_expr = ast.unparse(node)
            if node_expr in self._sub:
                return ast.Name(id=self._sub[node_expr])
        return super().visit(node)

    def visit_Call(self, node: ast.Call) -> ast.Call:
        return ast.Call(
            func=node.func,
            args=[self.visit(arg) for arg in node.args],
            keywords=[],
        )


def rename_variables(expr: str, sub: dict[str, str]) -> str:
    return ast.unparse(_ASTRenamer(sub).visit(ast.parse(expr)))
