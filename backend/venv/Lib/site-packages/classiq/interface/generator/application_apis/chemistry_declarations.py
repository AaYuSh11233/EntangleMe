from enum import Enum

from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    VQEResult,
)
from classiq.interface.generator.functions.type_name import Struct
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)

MOLECULE_PROBLEM_PARAM = ClassicalParameterDeclaration(
    name="molecule_problem", classical_type=Struct(name="MoleculeProblem")
)

FOCK_HAMILTONIAN_PROBLEM_PARAM = ClassicalParameterDeclaration(
    name="fock_hamiltonian_problem",
    classical_type=Struct(name="FockHamiltonianProblem"),
)
FOCK_HAMILTONIAN_SIZE = "get_field(get_field(fock_hamiltonian_problem_to_hamiltonian(fock_hamiltonian_problem)[0], 'pauli'), 'len')"


class ChemistryProblemType(Enum):
    MoleculeProblem = "molecule_problem"
    FockHamiltonianProblem = "fock_hamiltonian_problem"


MOLECULE_PROBLEM_TO_HAMILTONIAN = ClassicalFunctionDeclaration(
    name="molecule_problem_to_hamiltonian",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="problem", classical_type=Struct(name="MoleculeProblem")
        ),
    ],
    return_type=ClassicalArray(element_type=Struct(name="PauliTerm")),
)

FOCK_HAMILTONIAN_PROBLEM_TO_HAMILTONIAN = ClassicalFunctionDeclaration(
    name="fock_hamiltonian_problem_to_hamiltonian",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="problem", classical_type=Struct(name="FockHamiltonianProblem")
        ),
    ],
    return_type=ClassicalArray(element_type=Struct(name="PauliTerm")),
)


MOLECULE_GROUND_STATE_SOLUTION_POST_PROCESS = ClassicalFunctionDeclaration(
    name="molecule_ground_state_solution_post_process",
    positional_parameters=[
        ClassicalParameterDeclaration(
            name="problem", classical_type=Struct(name="MoleculeProblem")
        ),
        ClassicalParameterDeclaration(name="vqe_result", classical_type=VQEResult()),
    ],
    return_type=Struct(name="MoleculeResult"),
)

__all__ = [
    "FOCK_HAMILTONIAN_PROBLEM_TO_HAMILTONIAN",
    "MOLECULE_GROUND_STATE_SOLUTION_POST_PROCESS",
    "MOLECULE_PROBLEM_TO_HAMILTONIAN",
]
