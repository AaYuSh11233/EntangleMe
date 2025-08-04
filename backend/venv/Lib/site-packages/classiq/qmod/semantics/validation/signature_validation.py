from collections import Counter
from collections.abc import Sequence

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.model.quantum_function_declaration import (
    AnonPositionalArg,
    AnonQuantumOperandDeclaration,
)


def _check_duplicate_param_names(params: Sequence[AnonPositionalArg]) -> None:
    param_names = [param.name for param in params if param.name is not None]
    duplicates = [
        param_name for param_name, count in Counter(param_names).items() if count > 1
    ]
    if len(duplicates) > 0:
        raise ClassiqExpansionError(f"Duplicate parameter name {duplicates[0]!r}")


def validate_function_signature(params: Sequence[AnonPositionalArg]) -> None:
    _check_duplicate_param_names(params)
    for param in params:
        if isinstance(param, AnonQuantumOperandDeclaration):
            validate_function_signature(param.positional_arg_declarations)
