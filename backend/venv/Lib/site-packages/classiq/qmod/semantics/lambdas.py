from classiq.interface.helpers.backward_compatibility import zip_strict
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    AnonQuantumOperandDeclaration,
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_lambda_function import QuantumLambdaFunction

from classiq import AnonClassicalParameterDeclaration


def get_renamed_parameters(
    lambda_func: QuantumLambdaFunction,
) -> tuple[list[str], dict[str, QuantumOperandDeclaration], list[PortDeclaration]]:
    renamed_parameters: list[str] = []
    renamed_operands: dict[str, QuantumOperandDeclaration] = {}
    renamed_ports: list[PortDeclaration] = []
    for param, param_name in zip_strict(
        lambda_func.func_decl.positional_arg_declarations,
        lambda_func.pos_rename_params,
        strict=False,
    ):
        if isinstance(param, AnonClassicalParameterDeclaration):
            renamed_parameters.append(param_name)
        elif isinstance(param, AnonQuantumOperandDeclaration):
            renamed_operands[param_name] = param.rename(param_name)
        else:
            renamed_ports.append(param.rename(param_name))
    return renamed_parameters, renamed_operands, renamed_ports
