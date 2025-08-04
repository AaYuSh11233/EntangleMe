from typing import TYPE_CHECKING, Optional

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
    QuantumType,
)

from classiq.evaluators.quantum_type_utils import set_bounds


def _normalized_qnum(quantum_type: QuantumType) -> QuantumType:
    if not isinstance(quantum_type, QuantumNumeric):
        return quantum_type
    normalized_qnum = QuantumNumeric(
        size=quantum_type.size,
        is_signed=(
            quantum_type.is_signed
            if quantum_type.is_signed is not None
            else Expression(expr="False")
        ),
        fraction_digits=(
            quantum_type.fraction_digits
            if quantum_type.fraction_digits is not None
            else Expression(expr="0")
        ),
    )
    normalized_qnum.set_bounds(quantum_type.get_bounds())
    return normalized_qnum


def _same_shape(quantum_type_1: QuantumType, quantum_type_2: QuantumType) -> bool:
    if isinstance(quantum_type_1, QuantumBit) and isinstance(
        quantum_type_2, QuantumBit
    ):
        return True
    if (
        isinstance(quantum_type_1, QuantumNumeric)
        and isinstance(quantum_type_2, QuantumNumeric)
        and (
            not quantum_type_1.has_size_in_bits
            or not quantum_type_2.has_size_in_bits
            or quantum_type_1.size_in_bits == quantum_type_2.size_in_bits
        )
    ):
        return True
    if (
        isinstance(quantum_type_1, QuantumBitvector)
        and isinstance(quantum_type_2, QuantumBitvector)
        and (
            not quantum_type_1.has_constant_length
            or not quantum_type_2.has_constant_length
            or quantum_type_1.length_value == quantum_type_2.length_value
        )
        and _same_shape(quantum_type_1.element_type, quantum_type_2.element_type)
    ):
        return True
    return (
        isinstance(quantum_type_1, TypeName)
        and quantum_type_1.has_fields
        and isinstance(quantum_type_2, TypeName)
        and quantum_type_2.has_fields
        and quantum_type_1.name == quantum_type_2.name
        and all(
            _same_shape(
                quantum_type_1.fields[field_name], quantum_type_2.fields[field_name]
            )
            for field_name in quantum_type_1.fields
        )
    )


def _inject_qnum_type_attributes(
    from_type: QuantumType, to_type: QuantumNumeric
) -> QuantumNumeric:
    size: Optional[Expression]
    if from_type.has_size_in_bits:
        size = Expression(expr=str(from_type.size_in_bits))
    else:
        size = to_type.size
    if to_type.is_signed is not None:
        if to_type.is_signed.is_evaluated():
            is_signed = Expression(expr=str(to_type.sign_value))
        else:
            is_signed = Expression(expr="False")
    else:
        is_signed = None
    if to_type.fraction_digits is not None:
        if to_type.fraction_digits.is_evaluated():
            fraction_digits = Expression(expr=str(to_type.fraction_digits_value))
        else:
            fraction_digits = Expression(expr="0")
    else:
        fraction_digits = None
    if isinstance(from_type, QuantumNumeric) and not to_type.has_size_in_bits:
        if (
            is_signed is None
            and from_type.is_signed is not None
            and from_type.is_signed.is_evaluated()
        ):
            is_signed = from_type.is_signed
        if (
            fraction_digits is None
            and from_type.fraction_digits is not None
            and from_type.fraction_digits.is_evaluated()
        ):
            fraction_digits = from_type.fraction_digits
    if size is not None and is_signed is None:
        is_signed = Expression(expr="False")
    if size is not None and fraction_digits is None:
        fraction_digits = Expression(expr="0")
    updated_type = QuantumNumeric(
        size=size, is_signed=is_signed, fraction_digits=fraction_digits
    )
    updated_type.set_bounds(to_type.get_bounds())
    set_bounds(_normalized_qnum(from_type), updated_type)
    return updated_type


def _inject_qarray_type_attributes(
    from_type: QuantumType, to_type: QuantumBitvector
) -> Optional[QuantumBitvector]:
    if _same_shape(from_type, to_type):
        if TYPE_CHECKING:
            assert isinstance(from_type, QuantumBitvector)
        if to_type.has_length:
            length = to_type.length
        elif from_type.has_length:
            length = from_type.length
        elif from_type.has_size_in_bits:
            raise ClassiqExpansionError(
                f"Could not infer the length attribute of type {to_type.qmod_type_name}"
            )
        else:
            length = None
        element_type = inject_quantum_type_attributes(
            from_type.element_type, to_type.element_type
        )
    else:
        if to_type.has_constant_length:
            if (
                from_type.has_size_in_bits
                and from_type.size_in_bits % to_type.length_value != 0
            ):
                return None
            length = to_type.length
        elif from_type.has_size_in_bits:
            if not to_type.element_type.has_size_in_bits:
                raise ClassiqExpansionError(
                    f"Could not infer the length attribute of type "
                    f"{to_type.qmod_type_name}"
                )
            if from_type.size_in_bits % to_type.element_type.size_in_bits != 0:
                return None
            length = Expression(
                expr=str(from_type.size_in_bits // to_type.element_type.size_in_bits)
            )
        else:
            length = None
        if length is not None and from_type.has_size_in_bits:
            element_type = inject_quantum_type_attributes(
                QuantumBitvector(
                    length=Expression(
                        expr=str(from_type.size_in_bits // length.to_int_value())
                    )
                ),
                to_type.element_type,
            )
        else:
            element_type = inject_quantum_type_attributes(
                QuantumBitvector(), to_type.element_type
            )
    return QuantumBitvector(element_type=element_type, length=length)


def _inject_qstruct_type_attributes(
    from_type: QuantumType, to_type: TypeName
) -> Optional[TypeName]:
    if isinstance(from_type, TypeName) and from_type.name == to_type.name:
        fields = {
            field_name: inject_quantum_type_attributes(
                from_type.fields[field_name], to_type.fields[field_name]
            )
            for field_name in to_type.fields
        }
        if None in fields.values():
            return None
    elif not from_type.has_size_in_bits:
        fields = {
            field_name: inject_quantum_type_attributes(QuantumBitvector(), field_type)
            for field_name, field_type in to_type.fields.items()
        }
    else:
        initialized_fields = {
            field_name: field_type.has_size_in_bits
            for field_name, field_type in to_type.fields.items()
        }
        if sum(initialized_fields.values()) == len(initialized_fields) - 1:
            flexible_field_name = [
                field_name
                for field_name, is_initialized in initialized_fields.items()
                if not is_initialized
            ][0]
            flexible_field_size = from_type.size_in_bits - sum(
                field_type.size_in_bits
                for field_name, field_type in to_type.fields.items()
                if initialized_fields[field_name]
            )
            flexible_field_type = inject_quantum_type_attributes(
                QuantumBitvector(length=Expression(expr=str(flexible_field_size))),
                to_type.fields[flexible_field_name],
            )
            if flexible_field_type is None:
                return None
            fields = {
                field_name: (
                    flexible_field_type
                    if field_name == flexible_field_name
                    else inject_quantum_type_attributes(QuantumBitvector(), field_type)
                )
                for field_name, field_type in to_type.fields.items()
            }
        else:
            fields = {
                field_name: inject_quantum_type_attributes(
                    QuantumBitvector(), field_type
                )
                for field_name, field_type in to_type.fields.items()
            }
    classical_type = TypeName(name=to_type.name)
    classical_type.set_fields(fields)  # type:ignore[arg-type]
    return classical_type


def inject_quantum_type_attributes(
    from_type: QuantumType, to_type: QuantumType
) -> Optional[QuantumType]:
    for qmod_type in (from_type, to_type):
        if isinstance(qmod_type, TypeName) and not qmod_type.has_fields:
            raise ClassiqInternalExpansionError
    if to_type.has_size_in_bits and (
        (from_type.has_size_in_bits and to_type.size_in_bits != from_type.size_in_bits)
        or (from_type.minimal_size_in_bits > to_type.size_in_bits)
    ):
        return None
    if isinstance(to_type, QuantumBit):
        return QuantumBit()
    if isinstance(to_type, QuantumNumeric):
        return _inject_qnum_type_attributes(from_type, to_type)
    if isinstance(to_type, QuantumBitvector):
        return _inject_qarray_type_attributes(from_type, to_type)
    if isinstance(to_type, TypeName):
        return _inject_qstruct_type_attributes(from_type, to_type)
    raise ClassiqInternalExpansionError


def inject_quantum_type_attributes_inplace(
    from_type: QuantumType, to_type: QuantumType
) -> bool:
    updated_type = inject_quantum_type_attributes(from_type, to_type)
    if updated_type is None:
        return False
    if isinstance(to_type, QuantumBit) and isinstance(updated_type, QuantumBit):
        return True
    if isinstance(to_type, QuantumNumeric) and isinstance(updated_type, QuantumNumeric):
        to_type.size = updated_type.size
        to_type.is_signed = updated_type.is_signed
        to_type.fraction_digits = updated_type.fraction_digits
        to_type.set_bounds(updated_type.get_bounds())
        return True
    if isinstance(to_type, QuantumBitvector) and isinstance(
        updated_type, QuantumBitvector
    ):
        to_type.length = updated_type.length
        to_type.element_type = updated_type.element_type
        return True
    if (
        isinstance(to_type, TypeName)
        and to_type.has_fields
        and isinstance(updated_type, TypeName)
        and updated_type.has_fields
    ):
        to_type.set_fields(updated_type.fields)
        return True
    raise ClassiqInternalExpansionError
