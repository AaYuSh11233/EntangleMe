from collections.abc import Sequence
from enum import Enum
from typing import Any

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.generator.functions.classical_type import (
    StructMetaType,
)
from classiq.interface.generator.functions.concrete_types import ConcreteClassicalType
from classiq.interface.generator.functions.type_name import (
    TypeName,
)
from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
)
from classiq.interface.model.port_declaration import AnonPortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    AnonPositionalArg,
    AnonQuantumOperandDeclaration,
)

from classiq.evaluators.type_type_match import check_signature_match
from classiq.model_expansions.closure import FunctionClosure
from classiq.model_expansions.scope import Evaluated, QuantumVariable
from classiq.qmod.model_state_container import QMODULE
from classiq.qmod.qmod_parameter import CInt, get_qmod_type


def check_type_match(
    parameters: Sequence[AnonPositionalArg],
    arguments: list[Evaluated],
    function_name: str,
) -> None:
    if len(parameters) != len(arguments):
        raise ClassiqExpansionError(
            f"Function {function_name!r} takes {len(parameters)} arguments but "
            f"{len(arguments)} were given"
        )
    for parameter, evaluated_arg in zip(parameters, arguments):
        check_arg_type_match(evaluated_arg.value, parameter, function_name)


def check_arg_type_match(
    argument: Any, parameter: AnonPositionalArg, function_name: str
) -> None:
    message_prefix = (
        f"Argument {str(argument)!r} to parameter {parameter.name!r} of function "
        f"{function_name!r} has incompatible type; "
    )
    if isinstance(parameter, AnonPortDeclaration):
        error_message = message_prefix + "expected quantum variable"
        _check_qvar_type_match(argument, error_message)
    elif isinstance(parameter, AnonQuantumOperandDeclaration):
        if parameter.is_list:
            error_message = message_prefix + "expected list of operands"
            _check_operand_list_type_match(
                argument, parameter, function_name, error_message
            )
        else:
            error_message = message_prefix + "expected operand"
            _check_operand_type_match(argument, parameter, function_name, error_message)
    elif isinstance(parameter, AnonClassicalParameterDeclaration):
        error_message = (
            message_prefix + f"expected {_resolve_type_name(parameter.classical_type)}"
        )
        _check_classical_type_match(argument, parameter, error_message, function_name)
    else:
        raise ClassiqExpansionError(
            f"unexpected parameter declaration type: {type(parameter).__name__}"
        )


def _check_qvar_type_match(argument: Any, error_message: str) -> None:
    if not isinstance(argument, QuantumVariable):
        raise ClassiqExpansionError(error_message)


def _check_operand_list_type_match(
    argument: Any,
    parameter: AnonQuantumOperandDeclaration,
    function_name: str,
    error_message: str,
) -> None:
    if not isinstance(argument, list) or any(
        not isinstance(op, FunctionClosure) for op in argument
    ):
        raise ClassiqExpansionError(error_message)
    for idx, operand in enumerate(argument):
        if operand.positional_arg_declarations is not None:
            check_signature_match(
                parameter.positional_arg_declarations,
                operand.positional_arg_declarations,
                f"operand #{idx + 1} in parameter {parameter.name!r} "
                f"in function {function_name!r}",
            )


def _check_operand_type_match(
    argument: Any,
    parameter: AnonQuantumOperandDeclaration,
    function_name: str,
    error_message: str,
) -> None:
    if not isinstance(argument, FunctionClosure):
        raise ClassiqExpansionError(error_message)
    if argument.positional_arg_declarations is not None:
        check_signature_match(
            parameter.positional_arg_declarations,
            argument.positional_arg_declarations,
            f"operand {parameter.name!r} in function {function_name!r}",
        )


def _check_classical_type_match(
    argument: Any,
    parameter: AnonClassicalParameterDeclaration,
    error_message: str,
    function_name: str,
) -> None:
    classical_type = parameter.classical_type
    type_name = _resolve_type_name(classical_type)
    type_is_struct = (
        isinstance(classical_type, TypeName)
        and classical_type.name in QMODULE.type_decls
    )
    type_is_enum = (
        isinstance(classical_type, TypeName)
        and classical_type.name in QMODULE.enum_decls
    )
    arg_is_qvar = isinstance(argument, QmodSizedProxy)
    arg_is_builtin = argument.__class__.__module__ == "builtins"
    arg_is_int = isinstance(argument, int)
    arg_is_enum = isinstance(argument, Enum)
    arg_is_struct = isinstance(argument, QmodStructInstance)
    arg_struct_name = None if not arg_is_struct else argument.struct_declaration.name
    # FIXME: Remove suzuki_trotter overloading (CLS-2912)
    if function_name == "suzuki_trotter" and parameter.name == "pauli_operator":
        return
    if (
        arg_is_qvar
        or (arg_is_builtin and type_is_struct)
        or (arg_is_builtin and not arg_is_int and type_is_enum)
        or (arg_is_struct and (not type_is_struct or arg_struct_name != type_name))
        or (
            arg_is_enum
            and get_qmod_type(classical_type) != CInt
            and (not type_is_enum or type(argument).__name__ != type_name)
        )
    ):
        raise ClassiqExpansionError(error_message)


def _resolve_type_name(classical_type: ConcreteClassicalType) -> str:
    if isinstance(classical_type, StructMetaType):
        type_name = "Struct"
    else:
        type_name = get_qmod_type(classical_type).__name__
    if not isinstance(classical_type, TypeName):
        return type_name
    if type_name not in QMODULE.type_decls and type_name not in QMODULE.enum_decls:
        raise ClassiqExpansionError(f"Undefined type {type_name}")
    return type_name
