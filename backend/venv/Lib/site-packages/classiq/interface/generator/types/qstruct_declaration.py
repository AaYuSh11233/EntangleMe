from collections.abc import Mapping
from typing import TYPE_CHECKING

import pydantic

from classiq.interface.ast_node import HashableASTNode

if TYPE_CHECKING:
    from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType


class QStructDeclaration(HashableASTNode):
    name: str

    fields: Mapping[str, "ConcreteQuantumType"] = pydantic.Field(
        default_factory=dict,
        description="Dictionary of field names and their quantum types",
    )
