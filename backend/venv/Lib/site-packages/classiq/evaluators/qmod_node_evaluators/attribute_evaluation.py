import ast
from collections.abc import Mapping

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    Integer,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.handle_binding import FieldHandleBinding
from classiq.interface.model.quantum_type import (
    QuantumBitvector,
    QuantumNumeric,
    QuantumType,
)

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import QmodType


def _eval_type_attribute(
    expr_val: QmodAnnotatedExpression, node: ast.Attribute
) -> None:
    subject = node.value
    attr = node.attr

    subject_type = expr_val.get_type(subject)
    if isinstance(subject_type, QuantumType) and attr == "size":
        expr_val.set_type(node, Integer())
        if subject_type.has_size_in_bits:
            expr_val.set_value(node, subject_type.size_in_bits)
        else:
            expr_val.set_quantum_type_attr(node, subject, attr)
        return
    if isinstance(subject_type, (ClassicalArray, QuantumBitvector)) and attr == "len":
        expr_val.set_type(node, Integer())
        if subject_type.has_length:
            expr_val.set_value(node, subject_type.length_value)
        elif isinstance(subject_type, QuantumType):
            expr_val.set_quantum_type_attr(node, subject, attr)
        return
    if isinstance(subject_type, ClassicalTuple) and attr == "len":
        expr_val.set_type(node, Integer())
        expr_val.set_value(node, len(subject_type.element_types))
        return
    if isinstance(subject_type, QuantumNumeric):
        if attr == "is_signed":
            expr_val.set_type(node, Bool())
            if subject_type.has_sign:
                expr_val.set_value(node, subject_type.sign_value)
            elif subject_type.has_size_in_bits:
                expr_val.set_value(node, False)
            else:
                expr_val.set_quantum_type_attr(node, subject, attr)
            return
        if attr == "fraction_digits":
            expr_val.set_type(node, Integer())
            if subject_type.has_fraction_digits:
                expr_val.set_value(node, subject_type.fraction_digits_value)
            elif subject_type.has_size_in_bits:
                expr_val.set_value(node, 0)
            else:
                expr_val.set_quantum_type_attr(node, subject, attr)
            return
    raise ClassiqExpansionError(
        f"{subject_type.raw_qmod_type_name} has no attribute {attr!r}"
    )


def eval_attribute(expr_val: QmodAnnotatedExpression, node: ast.Attribute) -> None:
    subject = node.value
    attr = node.attr

    subject_type = expr_val.get_type(subject)
    if not isinstance(subject_type, TypeName) or (
        subject_type.has_fields and attr == "size"
    ):
        _eval_type_attribute(expr_val, node)
        return
    subject_fields: Mapping[str, QmodType]
    if subject_type.has_classical_struct_decl:
        subject_fields = subject_type.classical_struct_decl.variables
    elif subject_type.has_fields:
        subject_fields = subject_type.fields
    else:
        raise ClassiqInternalExpansionError
    if attr not in subject_fields:
        raise ClassiqExpansionError(
            f"{subject_type.raw_qmod_type_name} has no field {attr!r}"
        )
    expr_val.set_type(node, subject_fields[attr])

    if expr_val.has_value(subject):
        subject_value = expr_val.get_value(subject)
        if (
            not isinstance(subject_value, QmodStructInstance)
            or attr not in subject_value.fields
        ) and (not isinstance(subject_value, dict) or attr not in subject_value):
            raise ClassiqInternalExpansionError
        if isinstance(subject_value, QmodStructInstance):
            attr_value = subject_value.fields[attr]
        else:
            # dicts are supported because our foreign funcs return dicts instead of
            # QmodStructInstances
            # FIXME: Remove (CLS-3241)
            attr_value = subject_value[attr]
        expr_val.set_value(node, attr_value)
    elif expr_val.has_var(subject):
        subject_var = expr_val.get_var(subject)
        expr_val.set_var(node, FieldHandleBinding(base_handle=subject_var, field=attr))
        expr_val.remove_var(subject)
