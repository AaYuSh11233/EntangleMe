from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    Integer,
)
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)

GRID_ENTANGLER_GRAPH = ClassicalFunctionDeclaration(
    name="grid_entangler_graph",
    positional_parameters=[
        ClassicalParameterDeclaration(name="num_qubits", classical_type=Integer()),
        ClassicalParameterDeclaration(name="schmidt_rank", classical_type=Integer()),
        ClassicalParameterDeclaration(name="grid_randomization", classical_type=Bool()),
    ],
    return_type=ClassicalArray(element_type=ClassicalArray(element_type=Integer())),
)

HYPERCUBE_ENTANGLER_GRAPH = ClassicalFunctionDeclaration(
    name="hypercube_entangler_graph",
    positional_parameters=[
        ClassicalParameterDeclaration(name="num_qubits", classical_type=Integer()),
    ],
    return_type=ClassicalArray(element_type=ClassicalArray(element_type=Integer())),
)
