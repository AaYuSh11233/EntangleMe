from enum import IntEnum
from typing import Any, Optional, Union

import sympy

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import Enum, Struct, TypeName
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.helpers.backward_compatibility import zip_strict


def _copy_generative_flag(
    from_type: ClassicalType, to_type: Optional[ClassicalType]
) -> Optional[ClassicalType]:
    if to_type is None:
        return None
    if from_type.is_generative:
        return to_type.set_generative()
    return to_type


def infer_classical_type(value: Any) -> ClassicalType:
    if isinstance(value, IntEnum):
        return Enum(name=type(value).__name__)
    if isinstance(value, bool):
        return Bool()
    if isinstance(value, int):
        return Integer()
    if isinstance(value, (float, complex)):
        return Real()
    if isinstance(value, list):
        return ClassicalTuple(
            element_types=[infer_classical_type(item) for item in value]
        )
    if isinstance(value, QmodStructInstance):
        struct_name = value.struct_declaration.name
        classical_type = Struct(name=struct_name)
        classical_type.set_classical_struct_decl(
            StructDeclaration(
                name=struct_name,
                variables={
                    field_name: infer_classical_type(field_value)
                    for field_name, field_value in value.fields.items()
                },
            )
        )
        return classical_type
    # FIXME: Remove sympy compatibility (CLS-3214)
    if (
        isinstance(value, sympy.Basic)
        and len(value.free_symbols) == 0
        and value.is_complex
    ):
        return Real()
    raise ClassiqInternalExpansionError


def _inject_classical_array_attributes(
    from_type: ClassicalType, to_type: Union[ClassicalArray, ClassicalTuple]
) -> Optional[ClassicalType]:
    if isinstance(to_type, ClassicalArray):
        if isinstance(from_type, ClassicalArray):
            length: Optional[Expression]
            if from_type.has_length:
                if (
                    to_type.has_length
                    and from_type.length_value != to_type.length_value
                ):
                    return None
                length = from_type.length
            else:
                length = to_type.length
            element_type = inject_classical_type_attributes(
                from_type.element_type, to_type.element_type
            )
            if element_type is None:
                return None
            return ClassicalArray(element_type=element_type, length=length)
        if isinstance(from_type, ClassicalTuple):
            if (
                to_type.has_length
                and len(from_type.element_types) != to_type.length_value
            ):
                return None
            element_types = [
                inject_classical_type_attributes(element_type, to_type.element_type)
                for element_type in from_type.element_types
            ]
            if None in element_types:
                return None
            return ClassicalTuple(element_types=element_types)
        return None
    if isinstance(from_type, ClassicalArray):
        if from_type.has_length and from_type.length_value != len(
            to_type.element_types
        ):
            return None
        element_types = [
            inject_classical_type_attributes(from_type.element_type, element_type)
            for element_type in to_type.element_types
        ]
        if None in element_types:
            return None
        return ClassicalTuple(element_types=element_types)
    if isinstance(from_type, ClassicalTuple):
        if len(from_type.element_types) != len(to_type.element_types):
            return None
        element_types = [
            inject_classical_type_attributes(from_element_type, to_element_type)
            for from_element_type, to_element_type in zip_strict(
                from_type.element_types, to_type.element_types, strict=True
            )
        ]
        if None in element_types:
            return None
        return ClassicalTuple(element_types=element_types)
    return None


def _inject_classical_type_name_attributes(
    from_type: ClassicalType, to_type: TypeName
) -> Optional[ClassicalType]:
    if to_type.is_enum:
        if isinstance(from_type, Integer) or (
            isinstance(from_type, TypeName) and from_type.name == to_type.name
        ):
            return Enum(name=to_type.name)
        return None
    if to_type.has_classical_struct_decl:
        if not isinstance(from_type, TypeName) or from_type.name != to_type.name:
            return None
        classical_type = Struct(name=to_type.name)
        field_types = {
            field_name: inject_classical_type_attributes(
                from_type.classical_struct_decl.variables[field_name],
                to_type.classical_struct_decl.variables[field_name],
            )
            for field_name in to_type.classical_struct_decl.variables
        }
        if None in field_types.values():
            return None
        classical_type.set_classical_struct_decl(
            StructDeclaration(name=to_type.name, variables=field_types)
        )
        return classical_type
    return None


def inject_classical_type_attributes(
    from_type: ClassicalType, to_type: ClassicalType
) -> Optional[ClassicalType]:
    if isinstance(to_type, Bool):
        if isinstance(from_type, Bool):
            return _copy_generative_flag(to_type, Bool())
        return None
    if isinstance(to_type, Integer):
        if isinstance(from_type, (Integer, Real)) or (
            isinstance(from_type, TypeName) and from_type.is_enum
        ):
            return _copy_generative_flag(to_type, Integer())
        return None
    if isinstance(to_type, Real):
        if isinstance(from_type, (Integer, Real)) or (
            isinstance(from_type, TypeName) and from_type.is_enum
        ):
            return _copy_generative_flag(to_type, Real())
        return None
    if isinstance(to_type, (ClassicalArray, ClassicalTuple)):
        return _copy_generative_flag(
            to_type, _inject_classical_array_attributes(from_type, to_type)
        )
    if isinstance(to_type, TypeName):
        return _copy_generative_flag(
            to_type, _inject_classical_type_name_attributes(from_type, to_type)
        )
    return None
