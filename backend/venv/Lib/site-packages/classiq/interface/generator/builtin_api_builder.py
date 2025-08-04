from collections.abc import Iterable
from typing import Any

from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)


def populate_builtin_declarations(decls: Iterable[Any]) -> None:
    for decl in decls:
        if isinstance(decl, ClassicalFunctionDeclaration):
            ClassicalFunctionDeclaration.FOREIGN_FUNCTION_DECLARATIONS[decl.name] = decl
