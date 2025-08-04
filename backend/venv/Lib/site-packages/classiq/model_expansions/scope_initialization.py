from collections.abc import Sequence

from classiq.interface.exceptions import ClassiqError
from classiq.interface.generator.constant import Constant
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.model import MAIN_FUNCTION_NAME, Model
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import PositionalArg

from classiq.evaluators.classical_expression import (
    evaluate_classical_expression,
)
from classiq.evaluators.parameter_types import (
    evaluate_type_in_quantum_symbol,
)
from classiq.model_expansions.closure import FunctionClosure, GenerativeFunctionClosure
from classiq.model_expansions.scope import Evaluated, QuantumSymbol, Scope
from classiq.qmod.builtins import BUILTIN_CONSTANTS
from classiq.qmod.builtins.enums import BUILTIN_ENUM_DECLARATIONS
from classiq.qmod.builtins.functions import (
    CORE_LIB_DECLS,
    STD_QMOD_OPERATORS,
)
from classiq.qmod.builtins.structs import BUILTIN_STRUCT_DECLARATIONS
from classiq.qmod.model_state_container import QMODULE
from classiq.qmod.quantum_function import GenerativeQFunc
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator


def add_constants_to_scope(constants: list[Constant], scope: Scope) -> None:
    for constant in constants:
        scope[constant.name] = Evaluated(
            value=evaluate_classical_expression(constant.value, scope).value
        )


def add_functions_to_scope(
    functions: Sequence[NativeFunctionDefinition], scope: Scope
) -> None:
    for function in functions:
        if function.name not in scope:
            scope[function.name] = Evaluated(
                value=FunctionClosure.create(
                    name=function.name,
                    positional_arg_declarations=function.positional_arg_declarations,
                    body=function.body,
                    scope=Scope(parent=scope),
                )
            )


def add_generative_functions_to_scope(
    functions: Sequence[GenerativeQFunc], scope: Scope, override_atomic: bool = False
) -> None:
    for function in functions:
        name = function.func_decl.name
        if (
            name == MAIN_FUNCTION_NAME
            or name not in scope
            or (override_atomic and scope[name].value.is_atomic)
        ):
            scope[name] = Evaluated(
                value=GenerativeFunctionClosure.create(
                    name=name,
                    positional_arg_declarations=function.func_decl.positional_arg_declarations,
                    scope=Scope(parent=scope),
                    generative_blocks={"body": function},
                )
            )


def _init_builtins_scope(scope: Scope) -> None:
    for builtin_function in CORE_LIB_DECLS:
        scope[builtin_function.name] = Evaluated(
            value=FunctionClosure.create(
                name=builtin_function.name,
                positional_arg_declarations=builtin_function.positional_arg_declarations,
                scope=Scope(parent=scope),
                is_atomic=True,
            )
        )
    for builtin_function in STD_QMOD_OPERATORS:
        scope[builtin_function.name] = Evaluated(
            value=FunctionClosure.create(
                name=builtin_function.name,
                positional_arg_declarations=builtin_function.positional_arg_declarations,
                scope=Scope(parent=scope),
            )
        )
    for constant in BUILTIN_CONSTANTS:
        value = constant.value
        if not value.is_evaluated():
            raise ClassiqError(
                f"Unevaluated built-in constants not supported. Offending constant: "
                f"{constant.name} = {value}"
            )
        scope[constant.name] = Evaluated(value=value.value.value)


def add_entry_point_params_to_scope(
    parameters: Sequence[PositionalArg], main_closure: FunctionClosure
) -> None:
    for parameter in parameters:
        if isinstance(parameter, PortDeclaration):
            main_closure.scope[parameter.name] = Evaluated(
                value=QuantumSymbol(
                    handle=HandleBinding(name=parameter.name),
                    quantum_type=evaluate_type_in_quantum_symbol(
                        parameter.quantum_type, main_closure.scope, parameter.name
                    ),
                ),
                defining_function=main_closure,
            )
        elif isinstance(parameter, ClassicalParameterDeclaration):
            param_val = parameter.classical_type.get_classical_proxy(
                handle=HandleBinding(name=parameter.name)
            )
            main_closure.scope[parameter.name] = Evaluated(
                value=param_val,
                defining_function=main_closure,
            )


def init_top_level_scope(model: Model, scope: Scope) -> None:
    add_functions_to_scope(model.functions, scope)
    add_constants_to_scope(model.constants, scope)
    _init_builtins_scope(scope)


def init_builtin_types() -> None:
    QMODULE.enum_decls |= BUILTIN_ENUM_DECLARATIONS
    QMODULE.type_decls |= BUILTIN_STRUCT_DECLARATIONS
    QStructAnnotator().visit(BUILTIN_STRUCT_DECLARATIONS)
