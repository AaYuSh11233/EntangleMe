from typing import Annotated, Union

from pydantic import Field

from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    Estimation,
    Histogram,
    Integer,
    IQAERes,
    Real,
    StructMetaType,
    VQEResult,
)
from classiq.interface.generator.functions.type_name import Enum, TypeName
from classiq.interface.generator.types.qstruct_declaration import QStructDeclaration
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
    RegisterQuantumType,
)

ConcreteClassicalType = Annotated[
    Union[
        Integer,
        Real,
        Bool,
        StructMetaType,
        TypeName,
        ClassicalArray,
        ClassicalTuple,
        VQEResult,
        Histogram,
        Estimation,
        IQAERes,
    ],
    Field(discriminator="kind"),
]
ClassicalArray.model_rebuild()
ClassicalTuple.model_rebuild()

NativePythonClassicalTypes = (int, float, bool, list)
PythonClassicalPydanticTypes = (Enum,)

ConcreteQuantumType = Annotated[
    Union[QuantumBit, QuantumBitvector, QuantumNumeric, TypeName],
    Field(discriminator="kind", default_factory=QuantumBitvector),
]
QuantumBitvector.model_rebuild()
TypeName.model_rebuild()
QStructDeclaration.model_rebuild()
RegisterQuantumType.model_rebuild()

ConcreteType = Annotated[
    Union[
        Integer,
        Real,
        Bool,
        StructMetaType,
        TypeName,
        ClassicalArray,
        ClassicalTuple,
        VQEResult,
        Histogram,
        Estimation,
        IQAERes,
        QuantumBit,
        QuantumBitvector,
        QuantumNumeric,
    ],
    Field(discriminator="kind"),
]
