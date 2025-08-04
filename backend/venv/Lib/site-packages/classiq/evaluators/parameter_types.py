from typing import Optional, TypeVar, Union

import sympy

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
)
from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_name import (
    TypeName,
)
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    PositionalArg,
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
    QuantumType,
)

from classiq.evaluators.arg_type_match import check_type_match
from classiq.evaluators.classical_expression import (
    evaluate_classical_expression,
)
from classiq.evaluators.classical_type_inference import (
    infer_classical_type,
)
from classiq.evaluators.qmod_type_inference.quantum_type_inference import (
    inject_quantum_type_attributes,
)
from classiq.model_expansions.closure import FunctionClosure
from classiq.model_expansions.scope import (
    Evaluated,
    QuantumSymbol,
    QuantumVariable,
    Scope,
)


def evaluate_parameter_types_from_args(
    closure: FunctionClosure, signature_scope: Scope, arguments: list[Evaluated]
) -> list[PositionalArg]:
    parameters = closure.positional_arg_declarations
    function_name = closure.name
    check_type_match(parameters, arguments, function_name)

    for parameter, argument in zip(parameters, arguments):
        _update_scope(parameter, argument, closure)

    parameter_names = {parameter.name for parameter in parameters}
    for parameter in parameters:
        if isinstance(parameter, QuantumOperandDeclaration):
            parameter_value = closure.scope[parameter.name].value
            _update_operand_signature_environment(
                parameter_value, parameter_names, closure
            )

    return [
        _evaluate_type_from_arg(
            parameter,
            argument,
            Scope(parent=closure.scope | signature_scope),
            closure.name,
        )
        for parameter, argument in zip(parameters, arguments)
    ]


def _update_scope(
    parameter: PositionalArg, argument: Evaluated, closure: FunctionClosure
) -> None:
    if not isinstance(parameter, PortDeclaration):
        closure.scope[parameter.name] = argument
        return
    if parameter.direction is PortDeclarationDirection.Output:
        return
    quantum_var = argument.as_type(QuantumVariable)
    casted_argument = _cast(
        parameter.quantum_type,
        quantum_var,
        parameter.name,
    )
    closure.scope[parameter.name] = Evaluated(
        value=casted_argument, defining_function=closure
    )


NestedFunctionClosureT = Union[FunctionClosure, list["NestedFunctionClosureT"]]


def _update_operand_signature_environment(
    operand_val: NestedFunctionClosureT,
    parameter_names: set[str],
    closure: FunctionClosure,
) -> None:
    # We update the environment (parent) of the operand by adding closure.scope.data,
    # which includes the parameters that appear in the function's signature only.
    if isinstance(operand_val, list):
        for operand in operand_val:
            _update_operand_signature_environment(operand, parameter_names, closure)
        return
    if not isinstance(operand_val, FunctionClosure):
        raise ClassiqInternalExpansionError
    operand_val.signature_scope.update(
        {
            identifier: value
            for identifier, value in closure.scope.data.items()
            if identifier in parameter_names
        }
    )


def _cast(
    parameter_type: QuantumType, argument: QuantumVariable, param_name: str
) -> QuantumSymbol:
    updated_type = inject_quantum_type_attributes(argument.quantum_type, parameter_type)
    if updated_type is None:
        raise ClassiqExpansionError(
            f"Argument {str(argument)!r} of type "
            f"{argument.quantum_type.qmod_type_name} is incompatible with parameter "
            f"{param_name!r} of type {parameter_type.qmod_type_name}"
        )
    return QuantumSymbol(
        handle=HandleBinding(name=param_name), quantum_type=updated_type
    )


def _evaluate_type_from_arg(
    parameter: PositionalArg,
    argument: Evaluated,
    inner_scope: Scope,
    function_name: str,
) -> PositionalArg:
    # FIXME: Remove suzuki_trotter overloading (CLS-2912)
    if function_name == "suzuki_trotter" and parameter.name == "pauli_operator":
        return parameter
    if isinstance(parameter, ClassicalParameterDeclaration):
        updated_classical_type = evaluate_type_in_classical_symbol(
            parameter.classical_type.model_copy(), inner_scope, parameter.name
        )
        return ClassicalParameterDeclaration(
            name=parameter.name,
            classical_type=infer_classical_type(argument.value, updated_classical_type),
        )

    if not isinstance(parameter, PortDeclaration):
        return parameter

    updated_quantum_type: QuantumType = evaluate_type_in_quantum_symbol(
        parameter.quantum_type.model_copy(), inner_scope, parameter.name
    )
    if parameter.direction != PortDeclarationDirection.Output:
        arg_type = argument.as_type(QuantumVariable).quantum_type
        updated_output_quantum_type = inject_quantum_type_attributes(
            arg_type, updated_quantum_type
        )
        if updated_output_quantum_type is None:
            raise ClassiqExpansionError(
                f"Argument {str(argument.value)!r} of type "
                f"{arg_type.qmod_type_name} is incompatible with parameter "
                f"{parameter.name!r} of type {updated_quantum_type.qmod_type_name}"
            )
        updated_quantum_type = updated_output_quantum_type
    return parameter.model_copy(update={"quantum_type": updated_quantum_type})


def evaluate_type_in_quantum_symbol(
    type_to_update: QuantumType, scope: Scope, param_name: str
) -> ConcreteQuantumType:
    if isinstance(type_to_update, QuantumBitvector):
        return _evaluate_qarray_in_quantum_symbol(type_to_update, scope, param_name)
    elif isinstance(type_to_update, QuantumNumeric):
        return _evaluate_qnum_in_quantum_symbol(type_to_update, scope, param_name)
    elif isinstance(type_to_update, TypeName):
        return _evaluate_qstruct_in_quantum_symbol(type_to_update, scope, param_name)
    else:
        assert isinstance(type_to_update, QuantumBit)
        return type_to_update


def _evaluate_qarray_in_quantum_symbol(
    type_to_update: QuantumBitvector, scope: Scope, param_name: str
) -> QuantumBitvector:
    new_element_type = evaluate_type_in_quantum_symbol(
        type_to_update.element_type, scope, param_name
    )
    type_to_update.element_type = new_element_type
    if type_to_update.length is not None:
        new_length = _eval_expr(
            type_to_update.length,
            scope,
            int,
            type_to_update.type_name,
            "length",
            param_name,
        )
        if new_length is not None:
            type_to_update.length = Expression(expr=str(new_length))
    return type_to_update


def _evaluate_qnum_in_quantum_symbol(
    type_to_update: QuantumNumeric, scope: Scope, param_name: str
) -> QuantumNumeric:
    if type_to_update.size is None:
        return type_to_update
    new_size = _eval_expr(
        type_to_update.size,
        scope,
        int,
        type_to_update.type_name,
        "size",
        param_name,
    )
    if new_size is not None:
        type_to_update.size = Expression(expr=str(new_size))

    if type_to_update.is_signed is not None:
        new_is_sign = _eval_expr(
            type_to_update.is_signed,
            scope,
            bool,
            type_to_update.type_name,
            "sign",
            param_name,
        )
        if new_is_sign is not None:
            type_to_update.is_signed = Expression(expr=str(new_is_sign))
    else:
        type_to_update.is_signed = Expression(expr="False")

    if type_to_update.fraction_digits is not None:
        new_fraction_digits = _eval_expr(
            type_to_update.fraction_digits,
            scope,
            int,
            type_to_update.type_name,
            "fraction digits",
            param_name,
        )
        if new_fraction_digits is not None:
            type_to_update.fraction_digits = Expression(expr=str(new_fraction_digits))
    else:
        type_to_update.fraction_digits = Expression(expr="0")

    return type_to_update


_EXPR_TYPE = TypeVar("_EXPR_TYPE")


def _eval_expr(
    expression: Expression,
    scope: Scope,
    expected_type: type[_EXPR_TYPE],
    type_name: str,
    attr_name: str,
    param_name: str,
) -> Optional[_EXPR_TYPE]:
    val = evaluate_classical_expression(expression, scope).value
    if expected_type is int and isinstance(val, float):
        val = int(val)
    if isinstance(val, expected_type):
        return val
    if isinstance(val, AnyClassicalValue) or (
        isinstance(val, sympy.Basic) and len(val.free_symbols) > 0
    ):
        return None
    raise ClassiqExpansionError(
        f"When inferring the type of parameter {param_name!r}: "
        f"{type_name} {attr_name} must be {expected_type.__name__}, got "
        f"{str(val)!r}"
    )


def _evaluate_qstruct_in_quantum_symbol(
    type_to_update: TypeName, scope: Scope, param_name: str
) -> TypeName:
    new_fields = {
        field_name: evaluate_type_in_quantum_symbol(field_type, scope, param_name)
        for field_name, field_type in type_to_update.fields.items()
    }
    type_to_update.set_fields(new_fields)
    return type_to_update


def evaluate_types_in_quantum_symbols(
    symbols: list[QuantumSymbol], scope: Scope
) -> list[QuantumSymbol]:
    return [
        QuantumSymbol(
            handle=symbol.handle,
            quantum_type=evaluate_type_in_quantum_symbol(
                symbol.quantum_type, scope, str(symbol.handle)
            ),
        )
        for symbol in symbols
    ]


def evaluate_type_in_classical_symbol(
    type_to_update: ClassicalType, scope: Scope, param_name: str
) -> ClassicalType:
    updated_type: ClassicalType
    if isinstance(type_to_update, ClassicalArray):
        length = type_to_update.length
        if length is not None:
            new_length = _eval_expr(
                length, scope, int, "classical array", "length", param_name
            )
            if new_length is not None:
                length = Expression(expr=str(new_length))
        updated_type = ClassicalArray(
            element_type=evaluate_type_in_classical_symbol(
                type_to_update.element_type, scope, param_name
            ),
            length=length,
        )
    elif isinstance(type_to_update, ClassicalTuple):
        updated_type = ClassicalTuple(
            element_types=[
                evaluate_type_in_classical_symbol(element_type, scope, param_name)
                for element_type in type_to_update.element_types
            ],
        )
    elif (
        isinstance(type_to_update, TypeName)
        and type_to_update.has_classical_struct_decl
    ):
        updated_type = TypeName(name=type_to_update.name)
        updated_type.set_classical_struct_decl(
            type_to_update.classical_struct_decl.model_copy(
                update=dict(
                    variables={
                        field_name: evaluate_type_in_classical_symbol(
                            field_type, scope, param_name
                        )
                        for field_name, field_type in type_to_update.classical_struct_decl.variables.items()
                    }
                )
            )
        )
    else:
        updated_type = type_to_update
    if type_to_update.is_generative:
        updated_type.set_generative()
    return updated_type
