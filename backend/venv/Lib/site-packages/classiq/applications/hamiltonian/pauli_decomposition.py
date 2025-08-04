from typing import Union

import numpy as np
from sympy import fwht

from classiq.applications.combinatorial_helpers.pauli_helpers.pauli_utils import (
    pauli_operator_to_sparse_hamiltonian,
)
from classiq.qmod import (  # type:ignore[attr-defined]
    Pauli,
    PauliTerm,
)
from classiq.qmod.builtins.structs import SparsePauliOp

ATOL = 1e-12
PAULI_MATRICES_DICT = {
    Pauli.I: np.array([[1, 0], [0, 1]], dtype=np.complex128),
    Pauli.Z: np.array([[1, 0], [0, -1]], dtype=np.complex128),
    Pauli.X: np.array([[0, 1], [1, 0]], dtype=np.complex128),
    Pauli.Y: np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
}


def _get_pauli_string(set_index: int, term_index: int, num_qubits: int) -> list[Pauli]:
    """
    The basis of 4^N Pauli strings on N qubits can be partitioned to 2^N sets, each contains 2^N Pauli strings.
    In the k-th set we have Pauli strings of the form s_1s_2...s_N, where s_j is in {I,Z} if k_j is 0,
    and in {X,iY} if k_j=1. The function get_pauli_string returns the m-th Pauli string in the k-th set of Pauli strings
    """

    # returns the Pauli (I,Z) or (iY, X) appearing in the pauli_index position for a given set
    def _get_paulis_for_set(set_index: int, pauli_index: int) -> tuple[Pauli, Pauli]:
        if (set_index >> pauli_index) & 1:
            return Pauli.Y, Pauli.X
        else:
            return Pauli.Z, Pauli.I

    return [
        (
            _get_paulis_for_set(set_index, s)[0]
            if (term_index >> s) & 1
            else _get_paulis_for_set(set_index, s)[1]
        )
        for s in range(num_qubits)
    ][::-1]


def _coefficents_for_set(mat: np.ndarray, set_index: int) -> list:
    """
    The 2^N coefficients in a 2^N x 2^N matrix that are decomposed to the elements
    in the k-th set are the indices [i,j] such that i^j=k
    The function coefficents_for_set returns the matrix entries that are decomposed to the same Pauli strigs set
    """
    return [mat[k, k ^ set_index] / len(mat) for k in range(len(mat))]


def _get_signed_coefficient(
    c: complex, k: int, i: int, is_hermitian: bool
) -> Union[complex, float]:
    # correct from iY to Y
    coef = complex((1j) ** ((i & k).bit_count()) * c)
    if is_hermitian:
        return coef.real
    else:
        return coef


def matrix_to_hamiltonian(
    mat: np.ndarray, tol: float = ATOL, is_hermitian: bool = True
) -> list[PauliTerm]:
    """
    The decomposition per set is done by the Walsh-Hadamard transform,
    since the transformation between {e_0,e_3} ({e_1,e_2}) to {I,Z} ({X,iY}) is the Hadamard matrix.
    """
    mat.shape[0] != 0, "matrix is of size 0"
    if is_hermitian:
        assert np.allclose(
            mat, np.conjugate(mat.T)
        ), "Matrix is not hermitian, please pass is_hermitian=False"
    assert mat.shape[0] == mat.shape[1], "Matrix is not square"
    mat_dimension = mat.shape[0]
    assert mat_dimension.bit_count() == 1, "Matrix dimension is not a power of 2"
    num_qubits = (mat_dimension - 1).bit_length()
    hamiltonian = []
    for k in range(2**num_qubits):
        coef = fwht(
            _coefficents_for_set(mat, k)
        )  # the transformation per set is given by the Walsh-Hadamard transform
        hamiltonian += [
            PauliTerm(
                pauli=_get_pauli_string(k, i, num_qubits),
                coefficient=_get_signed_coefficient(coef[i], k, i, is_hermitian),
            )
            for i in range(2**num_qubits)
            if abs(coef[i]) > tol
        ]
    return hamiltonian


def matrix_to_pauli_operator(
    mat: np.ndarray, tol: float = ATOL, is_hermitian: bool = True
) -> SparsePauliOp:
    """
    The decomposition per set is done by the Walsh-Hadamard transform,
    since the transformation between {e_0,e_3} ({e_1,e_2}) to {I,Z} ({X,iY}) is the Hadamard matrix.
    """
    return pauli_operator_to_sparse_hamiltonian(
        matrix_to_hamiltonian(mat, tol=tol, is_hermitian=is_hermitian)
    )


# convert a single puali string of length N to 2**N X 2**N matrix
def pauli_string_to_mat(seq: list[Pauli]) -> np.ndarray:
    real_matrix = PAULI_MATRICES_DICT[seq[0]]
    for p in seq[1:]:
        real_matrix = np.kron(real_matrix, PAULI_MATRICES_DICT[p])
    return real_matrix


def _sparse_pauli_to_list(operator: SparsePauliOp) -> list[PauliTerm]:
    terms_list = []
    for term in operator.terms:
        pauli_list = [Pauli.I for i in range(operator.num_qubits)]
        for p in term.paulis:  # type:ignore[attr-defined]
            pauli_list[p.index] = p.pauli
        terms_list.append(
            PauliTerm(coefficient=term.coefficient, pauli=list(reversed(pauli_list)))
        )
    return terms_list


# return matrix from hamiltonian
def hamiltonian_to_matrix(
    hamiltonian: Union[list[PauliTerm], SparsePauliOp],
) -> np.ndarray:
    if isinstance(hamiltonian, SparsePauliOp):
        hamiltonian = _sparse_pauli_to_list(hamiltonian)
    matrix = np.zeros(
        [2 ** len(hamiltonian[0].pauli), 2 ** len(hamiltonian[0].pauli)],
        dtype=np.complex_,
    )
    for p in hamiltonian:
        matrix += p.coefficient * pauli_string_to_mat(p.pauli)

    return matrix
