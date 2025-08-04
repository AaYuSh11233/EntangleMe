from collections.abc import Mapping
from enum import Enum

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import Real
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.functions.type_name import Struct
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_type import QuantumBit, QuantumBitvector

FUNCTION_PORT_NAME = "func_port"
OBJECTIVE_PORT_NAME = "obj_port"


class FinanceModelType(Enum):
    LogNormal = "log_normal"
    Gaussian = "gaussian"


FINANCE_FUNCTION_PORT_SIZE_MAPPING: Mapping[FinanceModelType, str] = {
    FinanceModelType.Gaussian: "get_field(finance_model, 'num_qubits') + get_field(get_field(finance_model, 'rhos'), 'len') + floor(log(sum(get_field(finance_model, 'loss')), 2)) + 1",
    FinanceModelType.LogNormal: "get_field(finance_model, 'num_qubits')",
}


def _generate_finance_function(
    finance_model: FinanceModelType,
) -> NamedParamsQuantumFunctionDeclaration:
    return NamedParamsQuantumFunctionDeclaration(
        name=f"{finance_model.value}_finance",
        positional_arg_declarations=[
            ClassicalParameterDeclaration(
                name="finance_model",
                classical_type=Struct(name=f"{finance_model.name}Model"),
            ),
            ClassicalParameterDeclaration(
                name="finance_function", classical_type=Struct(name="FinanceFunction")
            ),
            PortDeclaration(
                name=FUNCTION_PORT_NAME,
                quantum_type=QuantumBitvector(
                    length=Expression(
                        expr=FINANCE_FUNCTION_PORT_SIZE_MAPPING[finance_model]
                    )
                ),
                direction=PortDeclarationDirection.Inout,
                type_modifier=TypeModifier.Mutable,
            ),
            PortDeclaration(
                name=OBJECTIVE_PORT_NAME,
                quantum_type=QuantumBit(),
                direction=PortDeclarationDirection.Inout,
                type_modifier=TypeModifier.Mutable,
            ),
        ],
    )


LOG_NORMAL_FINANCE_FUNCTION = _generate_finance_function(FinanceModelType.LogNormal)

GAUSSIAN_FINANCE_FUNCTION = _generate_finance_function(FinanceModelType.Gaussian)

LOG_NORMAL_FINANCE_POST_PROCESS = ClassicalFunctionDeclaration(
    name="log_normal_finance_post_process",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="finance_model", classical_type=Struct(name="LogNormalModel")
        ),
        ClassicalParameterDeclaration(
            name="estimation_method", classical_type=Struct(name="FinanceFunction")
        ),
        ClassicalParameterDeclaration(name="probability", classical_type=Real()),
    ],
    return_type=Real(),
)

GAUSSIAN_FINANCE_POST_PROCESS = ClassicalFunctionDeclaration(
    name="gaussian_finance_post_process",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="finance_model", classical_type=Struct(name="GaussianModel")
        ),
        ClassicalParameterDeclaration(
            name="estimation_method", classical_type=Struct(name="FinanceFunction")
        ),
        ClassicalParameterDeclaration(name="probability", classical_type=Real()),
    ],
    return_type=Real(),
)

__all__ = [
    "GAUSSIAN_FINANCE_FUNCTION",
    "GAUSSIAN_FINANCE_POST_PROCESS",
    "LOG_NORMAL_FINANCE_FUNCTION",
    "LOG_NORMAL_FINANCE_POST_PROCESS",
]
