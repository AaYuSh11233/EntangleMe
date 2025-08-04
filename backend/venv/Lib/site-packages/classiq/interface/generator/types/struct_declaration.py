from collections.abc import Mapping
from typing import Any

import pydantic

from classiq.interface.ast_node import HashableASTNode
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.functions.concrete_types import ConcreteClassicalType


class StructDeclaration(HashableASTNode):
    name: str

    variables: dict[str, ConcreteClassicalType] = pydantic.Field(
        default_factory=dict,
        description="Dictionary of variable names and their classical types",
    )

    def validate_fields(self, fields: Mapping[str, Any]) -> None:
        expected_field_names = list(self.variables.keys())
        received_field_names = list(fields.keys())
        if set(expected_field_names) != set(received_field_names):
            raise ClassiqValueError(
                f"Invalid fields for {self.name} instance. Expected fields "
                f"{expected_field_names}, got {received_field_names}"
            )
