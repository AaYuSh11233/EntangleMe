from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    Real,
    StructMetaType,
    VQEResult,
)
from classiq.interface.generator.functions.type_name import Struct
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)

OPTIMIZATION_PROBLEM_TO_HAMILTONIAN = ClassicalFunctionDeclaration(
    name="optimization_problem_to_hamiltonian",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="problem_type", classical_type=StructMetaType()
        ),
        ClassicalParameterDeclaration(name="penalty_energy", classical_type=Real()),
    ],
    return_type=ClassicalArray(element_type=Struct(name="PauliTerm")),
)

GET_OPTIMIZATION_SOLUTION = ClassicalFunctionDeclaration(
    name="get_optimization_solution",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="problem_type", classical_type=StructMetaType()
        ),
        ClassicalParameterDeclaration(
            name="vqe_result_handle", classical_type=VQEResult()
        ),
        ClassicalParameterDeclaration(name="penalty_energy", classical_type=Real()),
    ],
    return_type=ClassicalArray(
        element_type=Struct(name="CombinatorialOptimizationSolution")
    ),
)
