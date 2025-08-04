from typing import Any, Literal

import pydantic

from classiq.interface.exceptions import ClassiqInternalError
from classiq.interface.generator.functions.concrete_types import ConcreteClassicalType
from classiq.interface.helpers.pydantic_model_helpers import values_with_discriminator
from classiq.interface.model.parameter import Parameter


class AnonClassicalParameterDeclaration(Parameter):
    kind: Literal["ClassicalParameterDeclaration"]
    classical_type: ConcreteClassicalType

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(
            values, "kind", "ClassicalParameterDeclaration"
        )

    def rename(self, new_name: str) -> "ClassicalParameterDeclaration":
        if type(self) not in (
            AnonClassicalParameterDeclaration,
            ClassicalParameterDeclaration,
        ):
            raise ClassiqInternalError
        return ClassicalParameterDeclaration(
            **{
                **self.__dict__,
                "name": new_name,
                "kind": "ClassicalParameterDeclaration",
            }
        )


class ClassicalParameterDeclaration(AnonClassicalParameterDeclaration):
    name: str
