from collections.abc import Sequence
from itertools import chain, combinations, product
from math import factorial
from typing import Union

from openfermion.ops.operators.fermion_operator import FermionOperator
from openfermion.ops.operators.qubit_operator import QubitOperator

from classiq.applications.chemistry.mapping import FermionToQubitMapper
from classiq.applications.chemistry.op_utils import qubit_op_to_pauli_terms
from classiq.applications.chemistry.problems import FermionHamiltonianProblem
from classiq.qmod.builtins.structs import (
    SparsePauliOp,
)


def get_ucc_hamiltonians(
    problem: FermionHamiltonianProblem,
    mapper: FermionToQubitMapper,
    excitations: Union[int, Sequence[int]],
) -> list[SparsePauliOp]:
    """
    Computes the UCC hamiltonians of the given problem in the desired excitations,
    using the given mapper.

    Args:
        problem (FermionHamiltonianProblem): The fermion problem.
        mapper (FermionToQubitMapper): The mapper from fermion to qubits operators.
        excitations (int, Sequence[int]): A single desired excitation or an excitations
            list.

    Returns:
        The UCC hamiltonians.
    """
    if isinstance(excitations, int):
        excitations = [excitations]

    f_ops = (
        _hamiltonian_from_excitations(
            source, target, 1 / factorial(num_excitations) * 1j
        )
        for num_excitations in excitations
        for source, target in get_excitations(problem, num_excitations)
    )

    n_qubits = mapper.get_num_qubits(problem)
    return [
        qubit_op_to_pauli_terms(q_op, n_qubits)
        for f_op in f_ops
        if (q_op := mapper.map(f_op))
        not in (
            QubitOperator(),
            QubitOperator((), q_op.constant),
        )
    ]


def _hamiltonian_from_excitations(
    source: tuple[int, ...], target: tuple[int, ...], coeff: complex
) -> FermionOperator:
    op_string = " ".join(
        chain(
            (f"{i}^" for i in source),
            (f"{i}" for i in target),
        )
    )
    dagger_op_string = " ".join(
        chain(
            (f"{i}^" for i in reversed(target)),
            (f"{i}" for i in reversed(source)),
        )
    )
    return FermionOperator(op_string, coeff) - FermionOperator(dagger_op_string, coeff)


def get_excitations(
    problem: FermionHamiltonianProblem, num_excitations: int
) -> set[tuple[tuple[int, ...], tuple[int, ...]]]:
    """
    Gets all the possible excitations of the given problem according to the
    given number of excitations, preserving the particles spin.

    Args:
        problem (FermionHamiltonianProblem): The fermion problem.
        num_excitations (int): Number of excitations.

    Returns:
        A set of all possible excitations, specified as a pair of source and target indices.
    """
    if num_excitations <= 0:
        return set()

    possible_excitations = chain(
        product(problem.occupied_alpha, problem.virtual_alpha),
        product(problem.occupied_beta, problem.virtual_beta),
    )
    single_excitations = combinations(possible_excitations, r=num_excitations)

    excitations: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    for excitation in single_excitations:
        # the zip converts a sequence of single excitations (e.g. [(0, 1), (2, 3), (4, 5)])
        # to the sequence of combined excitations (e.g. [(0, 2, 4), (1, 3, 5)])
        source, target = (set(gr) for gr in zip(*excitation))

        # filter out excitations with repetitions in source/target
        if len(source) == num_excitations and len(target) == num_excitations:
            excitations.add((tuple(source), tuple(target)))

    return excitations
