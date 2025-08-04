from typing import Annotated, Union

from pydantic import Field

from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.bounds import SetBoundsStatement
from classiq.interface.model.classical_if import ClassicalIf
from classiq.interface.model.control import Control
from classiq.interface.model.inplace_binary_operation import InplaceBinaryOperation
from classiq.interface.model.invert import Invert
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.phase_operation import PhaseOperation
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
)
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_lambda_function import QuantumLambdaFunction
from classiq.interface.model.repeat import Repeat
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)
from classiq.interface.model.within_apply_operation import (
    Action,
    Compute,
    Uncompute,
    WithinApply,
)

ConcreteQuantumStatement = Annotated[
    Union[
        QuantumFunctionCall,
        Allocate,
        ArithmeticOperation,
        AmplitudeLoadingOperation,
        VariableDeclarationStatement,
        BindOperation,
        InplaceBinaryOperation,
        Repeat,
        Power,
        Invert,
        ClassicalIf,
        Control,
        WithinApply,
        PhaseOperation,
        Block,
        Compute,
        Action,
        Uncompute,
        SetBoundsStatement,
    ],
    Field(..., discriminator="kind"),
]

StatementBlock = list[ConcreteQuantumStatement]

Block.model_rebuild()
Control.model_rebuild()
QuantumLambdaFunction.model_rebuild()
Repeat.model_rebuild()
Power.model_rebuild()
Invert.model_rebuild()
WithinApply.model_rebuild()
ClassicalIf.model_rebuild()
NativeFunctionDefinition.model_rebuild()
PhaseOperation.model_rebuild()
