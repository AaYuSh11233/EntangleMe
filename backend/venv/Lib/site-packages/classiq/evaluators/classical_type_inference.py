from typing import TYPE_CHECKING, Any, Union

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.expressions.proxies.classical.classical_array_proxy import (
    ClassicalSequenceProxy,
    _is_int,
)
from classiq.interface.generator.expressions.proxies.classical.classical_struct_proxy import (
    ClassicalStructProxy,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.helpers.backward_compatibility import zip_strict


def infer_classical_type(val: Any, classical_type: ClassicalType) -> ClassicalType:
    if isinstance(classical_type, TypeName):
        return _infer_classical_struct_type(val, classical_type)
    if isinstance(classical_type, (ClassicalArray, ClassicalTuple)):
        return _infer_classical_array_type(val, classical_type)
    return classical_type


def _infer_classical_struct_type(val: Any, classical_type: TypeName) -> ClassicalType:
    if not isinstance(val, (QmodStructInstance, ClassicalStructProxy)):
        return classical_type
    if classical_type.is_enum:
        raise ClassiqExpansionError(
            f"{classical_type.type_name!r} expected, got {str(val)!r}"
        )
    decl = classical_type.classical_struct_decl
    new_fields = {
        field_name: infer_classical_type(field_val, field_type)
        for (field_name, field_val), field_type in zip_strict(
            val.fields.items(),
            decl.variables.values(),
            strict=True,
        )
    }
    new_classical_type = TypeName(name=decl.name)
    new_classical_type.set_classical_struct_decl(
        StructDeclaration(name=decl.name, variables=new_fields)
    )
    return new_classical_type


def _infer_classical_array_type(
    val: Any, classical_type: Union[ClassicalArray, ClassicalTuple]
) -> ClassicalType:
    if isinstance(val, ClassicalSequenceProxy):
        val_length = val.length
    elif isinstance(val, list):
        val_length = len(val)
    elif isinstance(val, AnyClassicalValue):
        return classical_type
    else:
        raise ClassiqExpansionError(f"Array expected, got {str(val)!r}")
    if isinstance(val_length, int) and (
        (
            isinstance(classical_type, ClassicalArray)
            and classical_type.length is not None
            and classical_type.length.is_evaluated()
            and _is_int(classical_type.length.value.value)
            and val_length != (type_length := int(classical_type.length.value.value))
        )
        or (
            isinstance(classical_type, ClassicalTuple)
            and val_length != (type_length := classical_type.length)
        )
    ):
        raise ClassiqExpansionError(
            f"Type mismatch: Argument has {val_length} items but "
            f"{type_length} expected"
        )
    new_classical_type = _infer_inner_array_types(classical_type, val, val_length)
    if classical_type.is_generative:
        new_classical_type.set_generative()
    return new_classical_type


def _infer_inner_array_types(
    classical_type: ClassicalType, val: Any, val_length: Any
) -> ClassicalType:
    if isinstance(classical_type, ClassicalTuple):
        return ClassicalTuple(
            element_types=(
                infer_classical_type(val[idx], element_type)
                for idx, element_type in enumerate(classical_type.element_types)
            ),
        )
    if TYPE_CHECKING:
        assert isinstance(classical_type, ClassicalArray)
    if _is_int(val_length) and val_length != 0:
        return ClassicalTuple(
            element_types=(
                infer_classical_type(val[i], classical_type.element_type)
                for i in range(int(val_length))
            ),
        )
    element_type: ClassicalType
    if val_length == 0:
        element_type = classical_type.element_type
    else:
        element_type = infer_classical_type(val[0], classical_type.element_type)
    if _is_int(val_length):
        length = Expression(expr=str(int(val_length)))
    else:
        length = None
    return ClassicalArray(element_type=element_type, length=length)
