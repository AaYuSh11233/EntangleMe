from classiq.interface.exceptions import ClassiqExpansionError, ClassiqValueError
from classiq.interface.generator.functions.classical_type import ClassicalArray
from classiq.interface.generator.functions.concrete_types import ConcreteClassicalType
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
    PositionalArg,
)

from classiq import ClassicalParameterDeclaration


def validate_main_function(func: NamedParamsQuantumFunctionDeclaration) -> None:
    for param in func.positional_arg_declarations:
        _validate_main_param(param)


def _validate_main_param(param: PositionalArg) -> None:
    if isinstance(param, ClassicalParameterDeclaration):
        _validate_main_classical_param_type(param.classical_type, param.name)
    if isinstance(param, PortDeclaration):
        _validate_main_quantum_param_type(param)


def _validate_main_classical_param_type(
    param: ConcreteClassicalType, param_name: str
) -> None:
    if isinstance(param, ClassicalArray):
        if param.length is None:
            raise ClassiqExpansionError(
                f"Classical array parameter {param_name!r} of function 'main' must "
                f"specify array length",
            )
        _validate_main_classical_param_type(param.element_type, param_name)


def _validate_main_quantum_param_type(param: PortDeclaration) -> None:
    if param.direction != PortDeclarationDirection.Output:
        raise ClassiqValueError("Function 'main' cannot declare quantum inputs")
