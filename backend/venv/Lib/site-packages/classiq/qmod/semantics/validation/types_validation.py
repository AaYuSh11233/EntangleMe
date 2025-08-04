from collections.abc import Sequence
from typing import Union

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.generator.types.enum_declaration import EnumDeclaration
from classiq.interface.generator.types.qstruct_declaration import QStructDeclaration
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.model.quantum_type import QuantumBitvector

from classiq.qmod.builtins.enums import BUILTIN_ENUM_DECLARATIONS
from classiq.qmod.builtins.structs import BUILTIN_STRUCT_DECLARATIONS
from classiq.qmod.model_state_container import QMODULE

TYPE_EXISTS_ERROR_MESSAGE = "Type {!r} already exists"


def check_duplicate_types(
    types: Sequence[Union[EnumDeclaration, StructDeclaration, QStructDeclaration]],
) -> None:
    known_types = {type_.name for type_ in BUILTIN_ENUM_DECLARATIONS.values()}
    known_types |= {type_.name for type_ in BUILTIN_STRUCT_DECLARATIONS.values()}
    for type_ in types:
        if type_.name in known_types:
            raise ClassiqExpansionError(TYPE_EXISTS_ERROR_MESSAGE.format(type_.name))
        else:
            known_types.add(type_.name)


def _check_qstruct_flexibility(qstruct: QStructDeclaration) -> None:
    _check_qstruct_no_array_without_size_and_element_size(qstruct)
    _check_qstruct_at_most_one_type_without_size(qstruct)


def _check_qstruct_no_array_without_size_and_element_size(
    qstruct: QStructDeclaration,
) -> None:
    offending_array_fields = [
        field_name
        for field_name, field_type in qstruct.fields.items()
        if isinstance(field_type, QuantumBitvector)
        and not field_type.has_length
        and not field_type.element_type.has_size_in_bits
    ]
    if len(offending_array_fields) > 0:
        raise ClassiqExpansionError(
            f"Quantum struct {qstruct.name} contains arrays whose neither length "
            f"nor element size are constants. Offending fields: "
            f"{', '.join(offending_array_fields)}"
        )


def _check_qstruct_at_most_one_type_without_size(qstruct: QStructDeclaration) -> None:
    fields_without_size = [
        field_name
        for field_name, field_type in qstruct.fields.items()
        if not field_type.has_size_in_bits
    ]
    if len(fields_without_size) > 1:
        raise ClassiqExpansionError(
            f"Quantum struct {qstruct.name} has more than one field whose size is "
            f"not constant. Offending fields: {', '.join(fields_without_size)}"
        )


def _check_qstruct_fields_are_defined(qstruct: QStructDeclaration) -> None:
    for field_type in qstruct.fields.values():
        if (
            isinstance(field_type, TypeName)
            and field_type.name not in QMODULE.qstruct_decls
        ):
            raise ClassiqExpansionError(
                f"Quantum struct {field_type.name!r} is not defined."
            )


def _check_qstruct_has_fields(qstruct: QStructDeclaration) -> None:
    if len(qstruct.fields) == 0:
        raise ClassiqExpansionError(
            f"Quantum struct {qstruct.name!r} must have at least one field."
        )


def _check_qstruct_is_not_recursive(qstruct: QStructDeclaration) -> None:
    for main_field_name, main_field in qstruct.fields.items():
        if (
            not isinstance(main_field, TypeName)
            or main_field.name not in QMODULE.qstruct_decls
        ):
            continue
        main_field_qstruct = QMODULE.qstruct_decls[main_field.name]
        seen_qstructs = {qstruct.name}
        stack = [main_field_qstruct]
        while stack:
            qstruct = stack.pop()
            if qstruct.name in seen_qstructs:
                raise ClassiqExpansionError(
                    f"Declaration of field {main_field_name!r} in quantum struct "
                    f"{qstruct.name!r} creates a recursive definition."
                )
            seen_qstructs.add(qstruct.name)
            stack.extend(
                [
                    QMODULE.qstruct_decls[field.name]
                    for field in qstruct.fields.values()
                    if isinstance(field, TypeName)
                    and field.name in QMODULE.qstruct_decls
                ]
            )


def validate_qstruct(qstruct: QStructDeclaration) -> None:
    _check_qstruct_has_fields(qstruct)
    _check_qstruct_fields_are_defined(qstruct)
    _check_qstruct_is_not_recursive(qstruct)
    _check_qstruct_flexibility(qstruct)


def _check_cstruct_has_fields(cstruct: StructDeclaration) -> None:
    if len(cstruct.variables) == 0:
        raise ClassiqExpansionError(
            f"Classical struct {cstruct.name!r} must have at least one field."
        )


def validate_cstruct(cstruct: StructDeclaration) -> None:
    _check_cstruct_has_fields(cstruct)
