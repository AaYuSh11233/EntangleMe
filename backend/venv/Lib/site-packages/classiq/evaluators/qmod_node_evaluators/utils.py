from typing import Optional, Union, cast

import sympy

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumNumeric,
    QuantumScalar,
    QuantumType,
)

QmodType = Union[ClassicalType, QuantumType]
IntegerValueType = int
RealValueType = Union[float, complex]
NumberValueType = Union[IntegerValueType, RealValueType]
SYMPY_SYMBOLS = {sym: getattr(sympy, sym) for sym in sympy.__all__}


def is_classical_type(qmod_type: QmodType) -> bool:
    if isinstance(qmod_type, TypeName):
        return qmod_type.has_classical_struct_decl or qmod_type.is_enum
    return isinstance(qmod_type, ClassicalType)


def qnum_is_qbit(qmod_type: QuantumNumeric) -> bool:
    return (
        (not qmod_type.has_size_in_bits or qmod_type.size_in_bits == 1)
        and (not qmod_type.has_sign or not qmod_type.sign_value)
        and (not qmod_type.has_fraction_digits or qmod_type.fraction_digits_value == 0)
    )


def get_numeric_properties(
    qmod_type: QuantumScalar,
) -> tuple[Optional[int], Optional[bool], Optional[int]]:
    if isinstance(qmod_type, QuantumBit):
        return 1, False, 0
    if not isinstance(qmod_type, QuantumNumeric):
        raise ClassiqInternalExpansionError
    size = qmod_type.size_in_bits if qmod_type.has_size_in_bits else None
    is_signed_expr = qmod_type.is_signed
    if is_signed_expr is None:
        is_signed = False
    elif is_signed_expr.is_evaluated() and is_signed_expr.is_constant():
        is_signed = is_signed_expr.to_bool_value()
    else:
        is_signed = None
    fraction_digits_expr = qmod_type.fraction_digits
    if fraction_digits_expr is None:
        fraction_digits = 0
    elif fraction_digits_expr.is_evaluated() and fraction_digits_expr.is_constant():
        fraction_digits = fraction_digits_expr.to_int_value()
    else:
        fraction_digits = None
    return size, is_signed, fraction_digits


def qnum_is_qint(qmod_type: QuantumType) -> bool:
    return isinstance(qmod_type, QuantumBit) or (
        isinstance(qmod_type, QuantumNumeric)
        and (not qmod_type.has_sign or not qmod_type.sign_value)
        and (not qmod_type.has_fraction_digits or qmod_type.fraction_digits_value == 0)
    )


def element_types(
    classical_type: Union[ClassicalArray, ClassicalTuple],
) -> list[ClassicalType]:
    if isinstance(classical_type, ClassicalArray):
        return [classical_type.element_type]
    return cast(list[ClassicalType], classical_type.element_types)


def array_len(
    classical_type: Union[ClassicalArray, ClassicalTuple],
) -> Optional[int]:
    if isinstance(classical_type, ClassicalTuple):
        return len(classical_type.element_types)
    if classical_type.has_length:
        return classical_type.length_value
    return None


def is_numeric_type(qmod_type: QmodType) -> bool:
    return isinstance(qmod_type, (Integer, Real, QuantumScalar)) or (
        isinstance(qmod_type, TypeName) and qmod_type.is_enum
    )


def is_classical_integer(qmod_type: QmodType) -> bool:
    return isinstance(qmod_type, Integer) or (
        isinstance(qmod_type, TypeName) and qmod_type.is_enum
    )
