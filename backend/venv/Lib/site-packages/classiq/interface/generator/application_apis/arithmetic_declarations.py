from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import Integer, Real
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)

qft_const_adder_phase = ClassicalFunctionDeclaration(
    name="qft_const_adder_phase",
    positional_parameters=[
        ClassicalParameterDeclaration(name="bit_index", classical_type=Integer()),
        ClassicalParameterDeclaration(name="value", classical_type=Integer()),
        ClassicalParameterDeclaration(name="reg_len", classical_type=Integer()),
    ],
    return_type=Real(),
)
