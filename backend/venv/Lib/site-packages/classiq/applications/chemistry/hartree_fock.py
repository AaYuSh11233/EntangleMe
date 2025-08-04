from collections.abc import Sequence

from openfermion.ops import FermionOperator
from openfermion.ops.operators.qubit_operator import QubitOperator

from classiq.applications.chemistry.mapping import FermionToQubitMapper
from classiq.applications.chemistry.problems import FermionHamiltonianProblem


def get_hf_fermion_op(problem: FermionHamiltonianProblem) -> FermionOperator:
    """
    Constructs a fermion operator that creates the Hartree-Fock reference state in
    block-spin ordering.

    Args:
        problem (FermionHamiltonianProblem): The fermion problem. The Hartree-Fock
            fermion operator depends only on the number of spatial orbitals and the
            number of alpha and beta particles.

    Returns:
        The Hartree-Fock fermion operator.
    """
    return FermionOperator(" ".join(f"{i}^" for i in problem.occupied))


def get_hf_state(
    problem: FermionHamiltonianProblem, mapper: FermionToQubitMapper
) -> list[bool]:
    """
    Computes the qubits state after applying the Hartree-Fock operator defined by the
    given problem and mapper.

    The Qmod function `prepare_basis_state` can be used on the returned value to
    allocate and initialize the qubits array.

    Args:
        problem (FermionHamiltonianProblem): The fermion problem.
        mapper (FermionToQubitMapper): The mapper from fermion operator to qubits
            operator.

    Returns:
        The qubits state, given as a list of boolean values for each qubit.
    """
    hf_qubit_op = _get_hf_qubit_op(problem, mapper)
    num_qubits = mapper.get_num_qubits(problem)
    if not hf_qubit_op.terms:
        return [False] * num_qubits

    # All terms map the zero state to the same basis state
    first_term = next(iter(hf_qubit_op.terms.keys()))
    return _apply_term_on_zero_state(first_term, num_qubits)


def _get_hf_qubit_op(
    problem: FermionHamiltonianProblem, mapper: FermionToQubitMapper
) -> QubitOperator:
    hf_fermion_op = get_hf_fermion_op(problem)
    # In case of tapering: We need to taper the state, not the operator. This can be done by passing is_invariant=True
    # (even though the operator is not necessarily invariant).
    # Then, taper_off_qubits eliminates the qubits to taper off (up to a sign)
    # for each term in the Hamiltonian.
    return mapper.map(hf_fermion_op, is_invariant=True)


def _apply_term_on_zero_state(
    term: Sequence[tuple[int, str]], num_qubits: int
) -> list[bool]:
    state = [False] * num_qubits
    for qubit, pauli in term:
        if pauli in ("X", "Y"):
            state[qubit] = True
    return state
