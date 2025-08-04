from typing import TYPE_CHECKING

import pydantic

from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
)

if TYPE_CHECKING:
    from classiq.interface.model.statement_block import StatementBlock


class NativeFunctionDefinition(NamedParamsQuantumFunctionDeclaration):
    """
    Facilitates the creation of a user-defined composite function

    This class sets extra to forbid so that it can be used in a Union and not "steal"
    objects from other classes.
    """

    body: "StatementBlock" = pydantic.Field(
        default_factory=list, description="List of function calls to perform."
    )
