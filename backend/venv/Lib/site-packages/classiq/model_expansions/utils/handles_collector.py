import ast

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.visitor import NodeType, Visitor
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumExpressionOperation,
)

from classiq.model_expansions.visitors.variable_references import VarRefCollector


class _HandlesCollector(Visitor):
    def __init__(self) -> None:
        self.handles: list[HandleBinding] = []

    def visit_HandleBinding(self, handle: HandleBinding) -> None:
        self.handles.append(handle)

    def visit_Expression(self, expression: Expression) -> None:
        vrc = VarRefCollector(ignore_duplicated_handles=True, unevaluated=True)
        vrc.visit(ast.parse(expression.expr))
        self.handles.extend(vrc.var_handles)

    def visit_QuantumExpressionOperation(self, op: QuantumExpressionOperation) -> None:
        self.handles.extend(op.var_handles)
        self.generic_visit(op)


def extract_handles(node: NodeType) -> list[HandleBinding]:
    collector = _HandlesCollector()
    collector.visit(node)
    return collector.handles
