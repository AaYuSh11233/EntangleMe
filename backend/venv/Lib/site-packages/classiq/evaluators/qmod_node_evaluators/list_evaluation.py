import ast
from typing import Optional, cast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
    Real,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.quantum_type import QuantumBitvector, QuantumType

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import (
    element_types,
    is_classical_integer,
    is_classical_type,
)


def _list_allowed(left: ClassicalType, right: ClassicalType) -> bool:
    for type_1, type_2 in ((left, right), (right, left)):
        if isinstance(type_1, Real) or is_classical_integer(type_1):
            return isinstance(type_2, Real) or is_classical_integer(type_2)

    if isinstance(left, Bool):
        return isinstance(right, Bool)

    if isinstance(left, (ClassicalArray, ClassicalTuple)) and isinstance(
        right, (ClassicalArray, ClassicalTuple)
    ):
        return list_allowed(element_types(left) + element_types(right))

    if isinstance(left, TypeName) and left.has_classical_struct_decl:
        return isinstance(right, TypeName) and left.name == right.name

    return False


def _has_empty_tuple(classical_type: ClassicalType) -> bool:
    if isinstance(classical_type, ClassicalArray):
        return _has_empty_tuple(classical_type.element_type)
    if isinstance(classical_type, ClassicalTuple):
        return len(classical_type.element_types) == 0 or any(
            _has_empty_tuple(element_type)
            for element_type in classical_type.element_types
        )
    return False


def list_allowed(classical_types: list[ClassicalType]) -> bool:
    if len(classical_types) < 2:
        return True

    element_without_empty_tuple: Optional[ClassicalType] = None
    for classical_type in classical_types:
        if not _has_empty_tuple(classical_type):
            element_without_empty_tuple = classical_type
            break

    if element_without_empty_tuple is not None:
        return all(
            element_without_empty_tuple is other_type
            or _list_allowed(element_without_empty_tuple, other_type)
            for other_type in classical_types
        )
    # FIXME: optimize using ClassicalTuple.raw_type (CLS-3163)
    return all(
        element_type is other_type or _list_allowed(classical_types[0], other_type)
        for i, element_type in enumerate(classical_types[:-1])
        for other_type in classical_types[i + 1 :]
    )


def eval_list(expr_val: QmodAnnotatedExpression, node: ast.List) -> None:
    item_types = [expr_val.get_type(item) for item in node.elts]
    are_classical = [is_classical_type(item_type) for item_type in item_types]
    all_classical = all(are_classical)
    all_quantum = not any(are_classical)
    if not all_classical and not all_quantum:
        raise ClassiqExpansionError(
            "Lists cannot contain both classical and quantum expressions"
        )
    if len(item_types) > 0 and all_quantum:
        expr_val.set_concatenation(node, node.elts)
        if all(
            cast(QuantumType, item_type).has_size_in_bits for item_type in item_types
        ):
            total_size = sum(
                [cast(QuantumType, item_type).size_in_bits for item_type in item_types]
            )
            concat_type = QuantumBitvector(length=Expression(expr=str(total_size)))
        else:
            concat_type = QuantumBitvector()
        expr_val.set_type(node, concat_type)
        return
    if not list_allowed(cast(list[ClassicalType], item_types)):
        raise ClassiqExpansionError("All list items must have the same type")

    if all(expr_val.has_value(item) for item in node.elts):
        expr_val.set_value(node, [expr_val.get_value(item) for item in node.elts])
    expr_val.set_type(node, ClassicalTuple(element_types=item_types))
