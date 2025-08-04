import ast
from typing import Any

from classiq.interface.ast_node import ASTNode
from classiq.interface.debug_info.debug_info import DebugInfoCollection
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import ClassicalType
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.visitor import Transformer, Visitor
from classiq.interface.model.model import Model
from classiq.interface.model.port_declaration import AnonPortDeclaration

from classiq.model_expansions.transformers.model_renamer import ExprNormalizer


class ModelNormalizer(Visitor):
    def visit(self, node: Any) -> None:
        if isinstance(node, ASTNode):
            node.model_config["frozen"] = False
            node.source_ref = None
            node.back_ref = None
            if hasattr(node, "uuid"):
                node.uuid = None
        super().visit(node)

    def visit_Model(self, model: Model) -> None:
        model.debug_info = DebugInfoCollection()
        model.functions.sort(key=lambda x: x.name)
        self.generic_visit(model)

    def visit_Expression(self, expr: Expression) -> None:
        expr.expr = ast.unparse(ExprNormalizer().visit(ast.parse(expr.expr)))

    def visit_AnonPortDeclaration(self, decl: AnonPortDeclaration) -> None:
        decl.type_modifier = TypeModifier.Mutable


class ClearModelInternals(Transformer):
    def visit_Expression(self, expr: Expression) -> Expression:
        expr._evaluated_expr = None
        expr._try_to_immediate_evaluate()
        return expr

    def visit_ClassicalType(self, classical_type: ClassicalType) -> ClassicalType:
        return type(classical_type).model_validate_json(
            classical_type.model_dump_json()
        )
