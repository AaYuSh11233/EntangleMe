import ast
from typing import Optional, cast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
    ClassiqValueError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    Integer,
    Real,
)
from classiq.interface.helpers.text_utils import s
from classiq.interface.model.handle_binding import (
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.quantum_type import (
    QuantumBitvector,
    QuantumNumeric,
    QuantumScalar,
    QuantumType,
)

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import (
    QmodType,
    array_len,
    element_types,
    get_numeric_properties,
)
from classiq.model_expansions.arithmetic_compute_result_attrs import (
    compute_result_attrs_quantum_subscript,
)


def _eval_slice(expr_val: QmodAnnotatedExpression, node: ast.Subscript) -> None:
    subject = node.value
    slice_ = cast(ast.Slice, node.slice)
    start = cast(ast.AST, slice_.lower)
    stop = cast(ast.AST, slice_.upper)
    if slice_.step is not None:
        raise ClassiqExpansionError("Slice step is not supported")

    start_type = expr_val.get_type(start)
    stop_type = expr_val.get_type(stop)
    for index_type in (start_type, stop_type):
        if not isinstance(index_type, Integer):
            raise ClassiqExpansionError(
                f"Slice indices must be integers, not {index_type.raw_qmod_type_name}"
            )

    start_val: Optional[int] = None
    if expr_val.has_value(start):
        start_val = cast(int, expr_val.get_value(start))
        if start_val < 0:
            raise ClassiqExpansionError("Slice indices must be positive integers")
    stop_val: Optional[int] = None
    if expr_val.has_value(stop):
        stop_val = cast(int, expr_val.get_value(stop))
        if start_val is not None and stop_val < start_val:
            raise ClassiqExpansionError(
                "Slice upper bound must be greater or equal to the lower bound"
            )

    subject_type = expr_val.get_type(subject)
    slice_type: QmodType
    if isinstance(subject_type, ClassicalArray):
        if subject_type.has_length and (
            (start_val is not None and start_val >= subject_type.length_value)
            or (stop_val is not None and stop_val > subject_type.length_value)
        ):
            raise ClassiqExpansionError("Array index out of range")
        length_expr: Optional[Expression] = None
        if start_val is not None and stop_val is not None:
            length_expr = Expression(expr=str(stop_val - start_val))
        slice_type = ClassicalArray(
            element_type=subject_type.element_type, length=length_expr
        )
    elif isinstance(subject_type, ClassicalTuple):
        if start_val is not None and stop_val is not None:
            if start_val >= len(subject_type.element_types) or stop_val > len(
                subject_type.element_types
            ):
                raise ClassiqExpansionError("Array index out of range")
            slice_type = ClassicalTuple(
                element_types=subject_type.element_types[start_val:stop_val]
            )
        else:
            slice_type = subject_type.get_raw_type()
    elif isinstance(subject_type, QuantumBitvector):
        if start_val is not None and stop_val is not None:
            if subject_type.has_length and (
                start_val >= subject_type.length_value
                or stop_val > subject_type.length_value
            ):
                raise ClassiqExpansionError("Array index out of range")
            slice_length = Expression(expr=str(stop_val - start_val))
        else:
            slice_length = None
        slice_type = QuantumBitvector(
            element_type=subject_type.element_type, length=slice_length
        )
    else:
        raise ClassiqExpansionError(
            f"{subject_type.raw_qmod_type_name} is not subscriptable"
        )
    expr_val.set_type(node, slice_type)

    if start_val is None or stop_val is None:
        return
    if expr_val.has_value(subject):
        subject_val = expr_val.get_value(subject)
        expr_val.set_value(node, subject_val[start_val:stop_val])
    elif expr_val.has_var(subject):
        subject_var = expr_val.get_var(subject)
        expr_val.set_var(
            node,
            SlicedHandleBinding(
                base_handle=subject_var,
                start=Expression(expr=str(start_val)),
                end=Expression(expr=str(stop_val)),
            ),
        )
        expr_val.remove_var(subject)


def _eval_subscript(expr_val: QmodAnnotatedExpression, node: ast.Subscript) -> None:
    subject = node.value
    subscript = node.slice

    index_type = expr_val.get_type(subscript)
    if not isinstance(index_type, Integer):
        raise ClassiqExpansionError(
            f"Array indices must be integers or slices, not "
            f"{index_type.raw_qmod_type_name}"
        )

    sub_val: Optional[int] = None
    if expr_val.has_value(subscript):
        sub_val = cast(int, expr_val.get_value(subscript))
        if sub_val < 0:
            raise ClassiqExpansionError("Array indices must be positive integers")

    subject_type = expr_val.get_type(subject)
    sub_type: QmodType
    if isinstance(subject_type, (ClassicalArray, QuantumBitvector)):
        if (
            sub_val is not None
            and subject_type.has_length
            and sub_val >= subject_type.length_value
        ):
            raise ClassiqExpansionError("Array index out of range")
        sub_type = subject_type.element_type
    elif isinstance(subject_type, ClassicalTuple):
        if sub_val is not None:
            if sub_val >= len(subject_type.element_types):
                raise ClassiqExpansionError("Array index out of range")
            sub_type = subject_type.element_types[sub_val]
        else:
            raw_subject_type = subject_type.get_raw_type()
            if not isinstance(raw_subject_type, ClassicalArray):
                raise ClassiqInternalExpansionError
            sub_type = raw_subject_type.element_type
    else:
        raise ClassiqExpansionError(
            f"{subject_type.raw_qmod_type_name} is not subscriptable"
        )
    expr_val.set_type(node, sub_type)

    if sub_val is None:
        return
    if expr_val.has_value(subject):
        subject_val = expr_val.get_value(subject)
        expr_val.set_value(node, subject_val[sub_val])
    elif expr_val.has_var(subject):
        subject_var = expr_val.get_var(subject)
        expr_val.set_var(
            node,
            SubscriptHandleBinding(
                base_handle=subject_var, index=Expression(expr=str(sub_val))
            ),
        )
        expr_val.remove_var(subject)


def eval_subscript(expr_val: QmodAnnotatedExpression, node: ast.Subscript) -> None:
    if isinstance(node.slice, ast.Slice):
        _eval_slice(expr_val, node)
    else:
        _eval_subscript(expr_val, node)


def validate_quantum_subscript_index_properties(
    index_size: Optional[int],
    index_sign: Optional[bool],
    index_fraction_digits: Optional[int],
    array_len: Optional[int],
) -> None:
    if index_sign or (index_fraction_digits is not None and index_fraction_digits > 0):
        raise ClassiqValueError("Quantum index must be an unsigned integer")
    if array_len == 0:
        raise ClassiqValueError(
            "Classical arrays indexed by a quantum variable must not be empty"
        )
    if array_len is None or index_size is None:
        return
    if 2**index_size > array_len:
        adjective = "short"
    elif 2**index_size < array_len:
        adjective = "long"
    else:
        return
    raise ClassiqValueError(
        f"Array is too {adjective}. It has {array_len} item{s(array_len)}, but its "
        f"quantum index has {index_size} bit{s(index_size)}"
    )


def eval_quantum_subscript(
    expr_val: QmodAnnotatedExpression, node: ast.Subscript, machine_precision: int
) -> None:
    subject = node.value
    subscript = node.slice

    subject_type = expr_val.get_type(subject)
    if not isinstance(subject_type, (ClassicalArray, ClassicalTuple)) or not all(
        isinstance(element_type, (Integer, Real))
        for element_type in element_types(subject_type)
    ):
        raise ClassiqExpansionError(
            "Only classical numeric arrays may have quantum subscripts"
        )

    index_type = cast(QuantumType, expr_val.get_type(subscript))
    if not isinstance(index_type, QuantumScalar):
        raise ClassiqExpansionError("Quantum index must be an unsigned integer")
    validate_quantum_subscript_index_properties(
        *get_numeric_properties(index_type), array_len(subject_type)
    )

    expr_val.set_quantum_subscript(node, subject, subscript)
    if not expr_val.has_value(subject):
        expr_val.set_type(node, QuantumNumeric())
        return

    items = expr_val.get_value(subject)
    result_attrs = compute_result_attrs_quantum_subscript(items, machine_precision)
    expr_val.set_type(node, result_attrs.to_quantum_numeric())
