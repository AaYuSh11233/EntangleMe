import ast
from typing import Any


class OutOfPlaceNodeTransformer(ast.NodeVisitor):
    def generic_visit(self, node: ast.AST) -> ast.AST:
        new_fields: dict[str, Any] = {}
        for field, field_val in ast.iter_fields(node):
            if isinstance(field_val, list):
                new_fields[field] = [
                    new_val
                    for item in field_val
                    if (new_val := self.visit(item)) is not None
                ]
            elif isinstance(field_val, ast.AST):
                new_fields[field] = self.visit(field_val)
            else:
                new_fields[field] = field_val
        return type(node)(**new_fields)
