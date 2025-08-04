import ast
from _ast import AST
from collections.abc import Collection
from typing import Optional, Union, cast

import networkx as nx

from classiq.interface.exceptions import ClassiqArithmeticError
from classiq.interface.generator.arith.arithmetic_expression_validator import (
    DEFAULT_EXPRESSION_TYPE,
    DEFAULT_SUPPORTED_FUNC_NAMES,
    DEFAULT_SUPPORTED_NODE_TYPES,
    ExpressionValidator,
    SupportedNodesTypes,
)
from classiq.interface.generator.arith.ast_node_rewrite import (
    OUTPUT_SIZE,
    AstNodeRewrite,
)

_MULTIPLE_RESULTS_ERROR_MESSAGE: str = "Expression cannot contain multiple results"
_UNEXPECTED_ARITHMETIC_ERROR_MESSAGE: str = (
    "Quantum expressions that evaluate to a classical value are not supported"
)
_ALLOWED_MULTI_ARGUMENT_FUNCTIONS = ("min", "max")
Node = Union[str, float, int]


class ExpressionVisitor(ExpressionValidator):
    def __init__(
        self,
        supported_nodes: tuple[type[AST], ...],
        expression_type: str = DEFAULT_EXPRESSION_TYPE,
        supported_functions: Optional[set[str]] = None,
    ) -> None:
        super().__init__(supported_nodes, expression_type, supported_functions)
        self.graph = nx.DiGraph()

    @classmethod
    def rewrite_ast(cls, expression_ast: AST) -> AST:
        return AstNodeRewrite().visit(expression_ast)

    def visit_Compare(self, node: ast.Compare) -> None:
        self.validate_Compare(node)
        self.update_graph(node, node.left, node.comparators[0])
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self.validate_BinOp(node)
        self.update_graph(node, node.left, node.right)
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        self.update_graph(node, node.operand)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.validate_Call(node)
        self.update_graph(node, *node.args)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.update_graph(node, *node.values)
        self.generic_visit(node)

    def update_graph(
        self, child_node: SupportedNodesTypes, *parent_nodes: ast.AST
    ) -> None:
        child_node_id = AstNodeRewrite().extract_node_id(child_node)

        for parent_node in parent_nodes:
            self._validate_node_type(parent_node)
            parent_node_id = AstNodeRewrite().extract_node_id(parent_node)
            self.graph.add_edge(parent_node_id, child_node_id)

        mod_output_size = getattr(child_node, OUTPUT_SIZE, None)
        if mod_output_size:
            self.graph.nodes[child_node_id][OUTPUT_SIZE] = mod_output_size

            for node in parent_nodes:
                node = cast(SupportedNodesTypes, node)
                node_output_size = getattr(node, OUTPUT_SIZE, mod_output_size)

                new_output_size = min(mod_output_size, node_output_size)
                node.output_size = new_output_size  # type: ignore[union-attr]

                node_id = AstNodeRewrite().extract_node_id(node)
                self.graph.nodes[node_id][OUTPUT_SIZE] = new_output_size


class InDegreeLimiter:
    @staticmethod
    def _sort_in_edges(
        in_edges: Collection[tuple[Node, str]],
    ) -> list[tuple[Node, str]]:
        return sorted(
            in_edges,
            key=lambda edge_tuple: isinstance(edge_tuple[0], str),  # vars before consts
            reverse=True,
        )

    @staticmethod
    def _condition(graph: nx.DiGraph, node: str) -> bool:
        return graph.in_degree[node] > 2 and node in _ALLOWED_MULTI_ARGUMENT_FUNCTIONS

    @classmethod
    def _node_conversion(cls, graph: nx.DiGraph, node: str) -> nx.DiGraph:
        last_node_added = node
        for idx, in_edge in enumerate(cls._sort_in_edges(graph.in_edges(node))[2:]):
            graph.remove_edge(*in_edge)
            new_node = node + f"_copy_{idx}"
            graph.add_node(new_node)
            for out_edge in list(graph.out_edges(last_node_added)):
                graph.add_edge(new_node, out_edge[1])
                graph.remove_edge(*out_edge)
            graph.add_edge(last_node_added, new_node)
            graph.add_edge(in_edge[0], new_node)
            last_node_added = new_node
        return graph

    @classmethod
    def graph_conversion(cls, graph: nx.DiGraph) -> nx.DiGraph:
        for node in list(graph.nodes):
            if cls._condition(graph, node):
                graph = cls._node_conversion(graph, node)

        num_results = sum(int(graph.out_degree(node) == 0) for node in graph.nodes)
        if num_results > 1:
            raise ClassiqArithmeticError(_MULTIPLE_RESULTS_ERROR_MESSAGE)
        elif num_results == 0:
            raise ClassiqArithmeticError(_UNEXPECTED_ARITHMETIC_ERROR_MESSAGE)
        return graph


def parse_expression(
    expression: str,
    *,
    supported_nodes: tuple[type[AST], ...] = DEFAULT_SUPPORTED_NODE_TYPES,
    expression_type: str = DEFAULT_EXPRESSION_TYPE,
    supported_functions: Optional[set[str]] = None,
) -> nx.DiGraph:
    supported_functions = supported_functions or DEFAULT_SUPPORTED_FUNC_NAMES

    visitor = ExpressionVisitor(supported_nodes, expression_type, supported_functions)
    visitor.validate(expression)
    InDegreeLimiter.graph_conversion(graph=visitor.graph)
    return visitor.graph
