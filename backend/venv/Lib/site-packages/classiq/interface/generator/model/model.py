from abc import ABC

import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.generator.constant import Constant
from classiq.interface.generator.function_params import ArithmeticIODict
from classiq.interface.generator.types.enum_declaration import EnumDeclaration
from classiq.interface.generator.types.qstruct_declaration import QStructDeclaration
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.helpers.validation_helpers import is_list_unique
from classiq.interface.helpers.versioned_model import VersionedModel
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.quantum_type import RegisterQuantumTypeDict

TYPE_LIBRARY_DUPLICATED_TYPE_NAMES = (
    "Cannot have multiple struct types with the same name"
)


class ClassiqBaseModel(VersionedModel, ABC):
    """
    All the relevant data for evaluating execution in one place.
    """

    enums: list[EnumDeclaration] = pydantic.Field(
        default_factory=list,
        description="user-defined enums",
    )

    types: list[StructDeclaration] = pydantic.Field(
        default_factory=list,
        description="user-defined structs",
    )

    qstructs: list[QStructDeclaration] = pydantic.Field(
        default_factory=list,
        description="user-defined quantum structs",
    )

    constants: list[Constant] = pydantic.Field(
        default_factory=list,
    )

    classical_execution_code: str = pydantic.Field(
        description="The classical execution code of the model", default=""
    )

    execution_preferences: ExecutionPreferences = pydantic.Field(
        default_factory=ExecutionPreferences
    )

    @pydantic.field_validator("types")
    @classmethod
    def types_validator(cls, types: list[StructDeclaration]) -> list[StructDeclaration]:
        if not is_list_unique([struct_type.name for struct_type in types]):
            raise ClassiqValueError(TYPE_LIBRARY_DUPLICATED_TYPE_NAMES)

        return types


class ExecutionModel(ClassiqBaseModel):
    circuit_outputs: ArithmeticIODict = pydantic.Field(
        description="Mapping between a measured register name and its arithmetic type",
        default_factory=dict,
    )
    circuit_output_types: RegisterQuantumTypeDict = pydantic.Field(
        description="Mapping between a measured register name and its qmod type",
        default=dict(),
    )
    register_filter_bitstrings: dict[str, list[str]] = pydantic.Field(
        default_factory=dict,
    )

    circuit_execution_params: dict[str, ClassicalParameterDeclaration] = pydantic.Field(
        default_factory=dict,
        description="Mapping between a execution parameter name and its declaration",
    )
