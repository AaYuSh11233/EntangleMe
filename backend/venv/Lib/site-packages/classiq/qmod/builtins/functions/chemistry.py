from classiq.qmod.builtins.structs import (
    FockHamiltonianProblem,
    MoleculeProblem,
)
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray, CInt
from classiq.qmod.qmod_variable import QArray, QBit


@qfunc(external=True)
def molecule_ucc(
    molecule_problem: MoleculeProblem,
    excitations: CArray[CInt],
    qbv: QArray[QBit],
) -> None:
    pass


@qfunc(external=True)
def molecule_hva(
    molecule_problem: MoleculeProblem,
    reps: CInt,
    qbv: QArray[QBit],
) -> None:
    pass


@qfunc(external=True)
def molecule_hartree_fock(
    molecule_problem: MoleculeProblem,
    qbv: QArray[QBit],
) -> None:
    pass


@qfunc(external=True)
def fock_hamiltonian_ucc(
    fock_hamiltonian_problem: FockHamiltonianProblem,
    excitations: CArray[CInt],
    qbv: QArray[QBit],
) -> None:
    pass


@qfunc(external=True)
def fock_hamiltonian_hva(
    fock_hamiltonian_problem: FockHamiltonianProblem,
    reps: CInt,
    qbv: QArray[QBit],
) -> None:
    pass


@qfunc(external=True)
def fock_hamiltonian_hartree_fock(
    fock_hamiltonian_problem: FockHamiltonianProblem,
    qbv: QArray[QBit],
) -> None:
    pass
