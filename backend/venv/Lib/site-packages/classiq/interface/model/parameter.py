from typing import Optional

from classiq.interface.ast_node import ASTNode
from classiq.interface.exceptions import ClassiqError


class Parameter(ASTNode):
    name: Optional[str]

    def get_name(self) -> str:
        if self.name is None:
            raise ClassiqError("Cannot resolve parameter name")
        return self.name
