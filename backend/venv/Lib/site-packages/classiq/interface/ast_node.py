from typing import Any, Optional, TypeVar
from uuid import UUID

import pydantic
from typing_extensions import Self

from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)
from classiq.interface.source_reference import SourceReference

ASTNodeType = TypeVar("ASTNodeType", bound="ASTNode")


class ASTNode(HashablePydanticBaseModel):
    source_ref: Optional[SourceReference] = pydantic.Field(default=None)
    back_ref: Optional[UUID] = pydantic.Field(default=None)

    def _as_back_ref(self: Self) -> Self:
        return self


def reset_lists(
    ast_node: ASTNodeType, statement_block_fields: list[str]
) -> ASTNodeType:
    update: dict[str, Any] = {field: [] for field in statement_block_fields}
    if hasattr(ast_node, "uuid"):
        update["uuid"] = ast_node.uuid
    return ast_node.model_copy(update=update)


class HashableASTNode(ASTNode, HashablePydanticBaseModel):
    pass
