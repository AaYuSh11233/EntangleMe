import ast
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Union, cast

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalType,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_type import QuantumType

from classiq.evaluators.qmod_expression_visitors.out_of_place_node_transformer import (
    OutOfPlaceNodeTransformer,
)
from classiq.evaluators.qmod_node_evaluators.utils import QmodType, is_classical_type

QmodExprNodeId = int


@dataclass(frozen=True)
class QuantumSubscriptAnnotation:
    value: QmodExprNodeId
    index: QmodExprNodeId


@dataclass(frozen=True)
class QuantumTypeAttributeAnnotation:
    value: QmodExprNodeId
    attr: str


@dataclass(frozen=True)
class ConcatenationAnnotation:
    elements: list[QmodExprNodeId]


def qmod_val_to_str(val: Any) -> str:
    if isinstance(val, QmodStructInstance):
        fields = ", ".join(
            f"{field_name}={qmod_val_to_str(field_val)}"
            for field_name, field_val in val.fields.items()
        )
        return f"{val.struct_declaration.name}({fields})"
    if isinstance(val, list):
        return f"[{', '.join(qmod_val_to_str(item) for item in val)}]"
    if isinstance(val, Enum):
        return Enum.__str__(val)
    if isinstance(val, (int, float, bool, complex)):
        return str(val)
    raise ClassiqInternalExpansionError(
        f"Unrecognized value {str(val)!r} of type {type(val)}"
    )


class _ExprInliner(OutOfPlaceNodeTransformer):
    def __init__(self, expr_val: "QmodAnnotatedExpression") -> None:
        self._expr_val = expr_val

    def visit(self, node: ast.AST) -> Any:
        if self._expr_val.has_value(node):
            return ast.Name(id=qmod_val_to_str(self._expr_val.get_value(node)))
        if self._expr_val.has_var(node):
            return ast.Name(id=str(self._expr_val.get_var(node)))
        return super().visit(node)


class QmodAnnotatedExpression:
    def __init__(self, expr_ast: ast.AST) -> None:
        self.root = expr_ast
        self._node_mapping: dict[QmodExprNodeId, ast.AST] = {}
        self._values: dict[QmodExprNodeId, Any] = {}
        self._types: dict[QmodExprNodeId, QmodType] = {}
        self._classical_vars: dict[QmodExprNodeId, HandleBinding] = {}
        self._quantum_vars: dict[QmodExprNodeId, HandleBinding] = {}
        self._quantum_subscripts: dict[QmodExprNodeId, QuantumSubscriptAnnotation] = {}
        self._quantum_type_attrs: dict[
            QmodExprNodeId, QuantumTypeAttributeAnnotation
        ] = {}
        self._concatenations: dict[QmodExprNodeId, ConcatenationAnnotation] = {}

    def __str__(self) -> str:
        return ast.unparse(_ExprInliner(self).visit(self.root))

    def has_node(self, node_id: QmodExprNodeId) -> bool:
        return node_id in self._node_mapping

    def get_node(self, node_id: QmodExprNodeId) -> ast.AST:
        return self._node_mapping[node_id]

    def set_value(self, node: Union[ast.AST, QmodExprNodeId], value: Any) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        self._values[node] = value

    def get_value(self, node: Union[ast.AST, QmodExprNodeId]) -> Any:
        if isinstance(node, ast.AST):
            node = id(node)
        return self._values[node]

    def has_value(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._values

    def set_type(
        self, node: Union[ast.AST, QmodExprNodeId], qmod_type: QmodType
    ) -> None:
        if isinstance(node, ast.AST):
            node_id = id(node)
            self._node_mapping[node_id] = node
            node = id(node)
        self._types[node] = qmod_type

    def get_type(self, node: Union[ast.AST, QmodExprNodeId]) -> QmodType:
        if isinstance(node, ast.AST):
            node = id(node)
        return self._types[node]

    def get_quantum_type(self, node: Union[ast.AST, QmodExprNodeId]) -> QuantumType:
        if isinstance(node, ast.AST):
            node = id(node)
        qmod_type = self._types[node]
        if is_classical_type(qmod_type):
            raise ClassiqInternalExpansionError
        return cast(QuantumType, qmod_type)

    def get_classical_type(self, node: Union[ast.AST, QmodExprNodeId]) -> ClassicalType:
        if isinstance(node, ast.AST):
            node = id(node)
        qmod_type = self._types[node]
        if not is_classical_type(qmod_type):
            raise ClassiqInternalExpansionError
        return cast(ClassicalType, qmod_type)

    def set_var(self, node: Union[ast.AST, QmodExprNodeId], var: HandleBinding) -> None:
        var = var.collapse()
        if isinstance(node, ast.AST):
            node = id(node)
        if is_classical_type(self.get_type(node)):
            self._classical_vars[node] = var
        else:
            self._quantum_vars[node] = var

    def get_var(self, node: Union[ast.AST, QmodExprNodeId]) -> HandleBinding:
        if isinstance(node, ast.AST):
            node = id(node)
        return (self._classical_vars | self._quantum_vars)[node]

    def has_var(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        return self.has_classical_var(node) or self.has_quantum_var(node)

    def has_classical_var(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._classical_vars

    def has_quantum_var(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._quantum_vars

    def remove_var(self, node: Union[ast.AST, QmodExprNodeId]) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        if node in self._classical_vars:
            self._classical_vars.pop(node)
        else:
            self._quantum_vars.pop(node)

    def set_quantum_subscript(
        self,
        node: Union[ast.AST, QmodExprNodeId],
        value: Union[ast.AST, QmodExprNodeId],
        index: Union[ast.AST, QmodExprNodeId],
    ) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        if isinstance(value, ast.AST):
            value = id(value)
        if isinstance(index, ast.AST):
            index = id(index)
        self._quantum_subscripts[node] = QuantumSubscriptAnnotation(
            value=value, index=index
        )

    def has_quantum_subscript(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._quantum_subscripts

    def get_quantum_subscripts(
        self,
    ) -> dict[QmodExprNodeId, QuantumSubscriptAnnotation]:
        return self._quantum_subscripts

    def set_quantum_type_attr(
        self,
        node: Union[ast.AST, QmodExprNodeId],
        value: Union[ast.AST, QmodExprNodeId],
        attr: str,
    ) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        if isinstance(value, ast.AST):
            value = id(value)
        self._quantum_type_attrs[node] = QuantumTypeAttributeAnnotation(
            value=value, attr=attr
        )

    def has_quantum_type_attribute(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._quantum_type_attrs

    def get_quantum_type_attributes(
        self,
    ) -> dict[QmodExprNodeId, QuantumTypeAttributeAnnotation]:
        return self._quantum_type_attrs

    def set_concatenation(
        self,
        node: Union[ast.AST, QmodExprNodeId],
        elements: Sequence[Union[ast.AST, QmodExprNodeId]],
    ) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        inlined_elements: list[QmodExprNodeId] = []
        for element in elements:
            if isinstance(element, ast.AST):
                element = id(element)
            if element not in self._concatenations:
                inlined_elements.append(element)
            else:
                inlined_elements.extend(self._concatenations.pop(element).elements)
        self._concatenations[node] = ConcatenationAnnotation(elements=inlined_elements)

    def has_concatenation(self, node: Union[ast.AST, QmodExprNodeId]) -> bool:
        if isinstance(node, ast.AST):
            node = id(node)
        return node in self._concatenations

    def get_concatenations(self) -> dict[QmodExprNodeId, ConcatenationAnnotation]:
        return self._concatenations

    def get_classical_vars(self) -> dict[QmodExprNodeId, HandleBinding]:
        return self._classical_vars

    def get_quantum_vars(self) -> dict[QmodExprNodeId, HandleBinding]:
        return self._quantum_vars

    def clear_node_data(self, node: Union[ast.AST, QmodExprNodeId]) -> None:
        if isinstance(node, ast.AST):
            node = id(node)
        self._node_mapping.pop(node, None)
        self._values.pop(node, None)
        self._types.pop(node, None)
        self._classical_vars.pop(node, None)
        self._quantum_vars.pop(node, None)
        qs = self._quantum_subscripts.pop(node, None)
        if qs is not None:
            self.clear_node_data(qs.value)
            self.clear_node_data(qs.index)
        qta = self._quantum_type_attrs.pop(node, None)
        if qta is not None:
            self.clear_node_data(qta.value)
        cnct = self._concatenations.pop(node, None)
        if cnct is not None:
            for element in cnct.elements:
                self.clear_node_data(element)

    def _add_data_from(self, other: "QmodAnnotatedExpression") -> None:
        self._node_mapping |= other._node_mapping
        self._values |= other._values
        self._types |= other._types
        self._classical_vars |= other._classical_vars
        self._quantum_vars |= other._quantum_vars
        self._quantum_subscripts |= other._quantum_subscripts
        self._quantum_type_attrs |= other._quantum_type_attrs
        self._concatenations |= other._concatenations
