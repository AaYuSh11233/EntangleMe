from collections.abc import Sequence

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
)
from classiq.interface.model.port_declaration import AnonPortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    AnonPositionalArg,
    AnonQuantumOperandDeclaration,
)


def check_signature_match(
    decl_params: Sequence[AnonPositionalArg],
    op_params: Sequence[AnonPositionalArg],
    location_str: str,
) -> None:
    if len(decl_params) != len(op_params):
        raise ClassiqExpansionError(
            f"{location_str} should have {len(decl_params)} parameters, "
            f"not {len(op_params)}"
        )
    for idx, (decl_param, op_param) in enumerate(zip(decl_params, op_params)):
        message_prefix = f"Argument {idx} in {location_str} has incompatible type; "
        _check_type_match(op_param, decl_param, location_str, message_prefix)


def _check_type_match(
    op_param: AnonPositionalArg,
    decl_param: AnonPositionalArg,
    location_str: str,
    message_prefix: str,
) -> None:
    if isinstance(decl_param, AnonPortDeclaration):
        error_message = message_prefix + "expected quantum parameter"
        _check_qvar_type_match(op_param, error_message)
    elif isinstance(decl_param, AnonQuantumOperandDeclaration):
        if decl_param.is_list:
            error_message = message_prefix + "expected operand list parameter"
        else:
            error_message = message_prefix + "expected operand parameter"
        _check_operand_type_match(op_param, decl_param, location_str, error_message)
    elif isinstance(decl_param, AnonClassicalParameterDeclaration):
        error_message = (
            message_prefix + f"expected classical {decl_param.classical_type} parameter"
        )
        _check_classical_type_match(op_param, decl_param, error_message)
    else:
        raise ClassiqInternalExpansionError(
            f"unexpected parameter declaration type: {type(decl_param).__name__}"
        )


def _check_qvar_type_match(op_param: AnonPositionalArg, error_message: str) -> None:
    if not isinstance(op_param, AnonPortDeclaration):
        raise ClassiqExpansionError(error_message)


def _check_operand_type_match(
    op_param: AnonPositionalArg,
    decl_param: AnonQuantumOperandDeclaration,
    location_str: str,
    error_message: str,
) -> None:
    if (
        not isinstance(op_param, AnonQuantumOperandDeclaration)
        or decl_param.is_list ^ op_param.is_list
    ):
        raise ClassiqExpansionError(error_message)
    check_signature_match(
        decl_param.positional_arg_declarations,
        op_param.positional_arg_declarations,
        f"operand {decl_param.name} in {location_str}",
    )


def _check_classical_type_match(
    op_param: AnonPositionalArg,
    decl_param: AnonClassicalParameterDeclaration,
    error_message: str,
) -> None:
    if (
        not isinstance(op_param, AnonClassicalParameterDeclaration)
        or decl_param.classical_type.clear_flags()
        != op_param.classical_type.clear_flags()
    ):
        raise ClassiqExpansionError(error_message)
