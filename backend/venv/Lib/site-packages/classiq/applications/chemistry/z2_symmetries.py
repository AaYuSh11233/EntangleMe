from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
from openfermion.ops.operators.fermion_operator import FermionOperator
from openfermion.ops.operators.qubit_operator import QubitOperator
from openfermion.transforms import taper_off_qubits
from openfermion.utils.commutators import anticommutator, commutator

from classiq.interface.exceptions import ClassiqValueError

from classiq.applications.chemistry.mapping import FermionToQubitMapper, MappingMethod
from classiq.applications.chemistry.op_utils import (
    qubit_op_to_xz_matrix,
    xz_matrix_to_qubit_op,
)
from classiq.applications.chemistry.problems import FermionHamiltonianProblem


class Z2SymTaperMapper(FermionToQubitMapper):
    """
    Mapper between fermionic operators to qubits operators, using one of the supported
    mapping methods (see `MappingMethod`), and taking advantage of Z2 symmetries in
    order to taper off qubits.

    Attributes:
        method (MappingMethod): The mapping method.
        generators (tuple[QubitOperator, ...]): Generators representing the Z2
            symmetries.
        x_ops (tuple[QubitOperator, ...]): Single-qubit X operations, such that each
            operation anti-commutes with its matching generator and commutes with all
            other generators.
    """

    def __init__(
        self,
        generators: Sequence[QubitOperator],
        x_ops: Sequence[QubitOperator],
        method: MappingMethod = MappingMethod.JORDAN_WIGNER,
        sector: Optional[Sequence[int]] = None,
        tol: float = 1e-14,
    ) -> None:
        """
        Initializes a `Z2SymTaperMapper` object from the given configuration.

        Args:
            generators (Sequence[QubitOperator]): Generators representing the Z2
                symmetries.
            x_ops (Sequence[QubitOperator]): Single-qubit X operations, such that each
                operation anti-commutes with its matching generator and commutes with all
                other generators.
            method (MappingMethod): The mapping method.
            sector: (Sequence[int]): Symmetry sector coefficients, each is 1 or -1.
                If not specified, all coefficients defaults to 1.
            tol (float): Tolerance for trimming off terms.
        """
        super().__init__(method=method)

        self._validate_symmetries(generators, x_ops)

        self._generators = generators
        self._x_ops = x_ops
        self._tol = tol

        self.set_sector(sector or [1] * len(self._generators))

    @staticmethod
    def _validate_symmetries(
        generators: Sequence[QubitOperator],
        x_ops: Sequence[QubitOperator],
    ) -> None:
        if len(generators) != len(x_ops):
            raise ClassiqValueError(
                "Generators and X operations must have the same length."
            )

        for i, x_op in enumerate(x_ops):
            for j, gen in enumerate(generators):
                if i == j:
                    if anticommutator(x_op, gen) != QubitOperator():
                        raise ClassiqValueError(
                            f"x_{i}={x_op} and generator_{j}={gen} should anti-commute but don't."
                        )
                else:
                    if commutator(x_op, gen) != QubitOperator():
                        raise ClassiqValueError(
                            f"x_{i}={x_op} and generator_{j}={gen} should commute but don't."
                        )

    def set_sector(self, sector: Sequence[int]) -> None:
        """
        Sets the symmetry sector coefficients.

        Args:
            sector: (Sequence[int]): Symmetry sector coefficients, each is 1 or -1.
        """
        if len(sector) != len(self._generators):
            raise ClassiqValueError(
                "Sector must have the same length as the generators."
            )
        self._sector = sector

    @property
    def generators(self) -> tuple[QubitOperator, ...]:
        """
        Generators representing the Z2 symmetries.
        """
        return tuple(self._generators)

    @property
    def x_ops(self) -> tuple[QubitOperator, ...]:
        """
        Single-qubit X operations, such that each operation anti-commutes with its
        matching generator and commutes with all other generators.
        """
        return tuple(self._x_ops)

    def map(
        self,
        fermion_op: FermionOperator,
        *args: Any,
        is_invariant: bool = False,
        **kwargs: Any,
    ) -> QubitOperator:
        """
        Maps the given fermionic operator to qubits operator by using the
        mapper's method, and subsequently by tapering off qubits according to Z2
        symmetries.

        Args:
            fermion_op (FermionOperator): A fermionic operator.
            is_invariant (bool): If `False`, the operator is not necessarily in the
                symmetry subspace, and thus gets projected onto it before tapering.

        Returns:
            The mapped qubits operator.
        """
        qubit_op = super().map(fermion_op)
        sectored_x_ops = [s * x_op for s, x_op in zip(self._sector, self._x_ops)]

        if not is_invariant:
            qubit_op = _project_operator_to_subspace(qubit_op, self._generators)

        block_diagonal_op = self._block_diagnolize(qubit_op)
        tapered_op = taper_off_qubits(block_diagonal_op, sectored_x_ops)
        if TYPE_CHECKING:
            assert isinstance(tapered_op, QubitOperator)
        tapered_op.compress(self._tol)
        return tapered_op

    def get_num_qubits(self, problem: FermionHamiltonianProblem) -> int:
        """
        Gets the number of qubits after mapping the given problem into qubits space.

        Args:
            problem (FermionHamiltonianProblem): The fermion problem.

        Returns:
            The number of qubits.
        """
        return super().get_num_qubits(problem) - len(self._generators)

    @classmethod
    def from_problem(
        cls,
        problem: FermionHamiltonianProblem,
        method: MappingMethod = MappingMethod.JORDAN_WIGNER,
        sector_from_hartree_fock: bool = True,
        tol: float = 1e-14,
    ) -> "Z2SymTaperMapper":
        """
        Initializes a `Z2SymTaperMapper` object from a fermion problem (i.e. computing
        the Z2 symmetries from the problem definition).

        Args:
            problem (FermionHamiltonianProblem): The fermion problem.
            method (MappingMethod): The mapping method.
            sector_from_hartree_fock (bool): Whether to compute the symmetry sector
                coefficients according to the Hartree-Fock state.
            tol (float): Tolerance for trimming off terms.

        Returns:
            The Z2 symmetries taper mapper.
        """
        mapper = FermionToQubitMapper(method)
        n_qubits = mapper.get_num_qubits(problem)

        qubit_op = mapper.map(problem.fermion_hamiltonian)
        qubit_op.compress(tol)

        generators = _get_z2_symmetries_generators(qubit_op, n_qubits)
        x_ops = _get_x_ops_for_generators(generators, n_qubits)

        sector: Optional[list[int]] = None
        if sector_from_hartree_fock:
            from classiq.applications.chemistry.hartree_fock import get_hf_state

            if not (generators[:, :n_qubits] == 0).all():
                raise ClassiqValueError(
                    "The Hartree-Fock state is not in the symmetry space spanned by the generators, please set `sector_from_hartree_fock=False`. You can later set the sector manually with `set_sector`."
                )

            state = get_hf_state(problem, mapper)
            sector = _get_sector_for_basis_state(generators[:, n_qubits:], state)

        return cls(
            generators=[xz_matrix_to_qubit_op(gen) for gen in generators],
            x_ops=x_ops,
            sector=sector,
            tol=tol,
            method=method,
        )

    @cached_property
    def _block_diagonalizing_clifford(self) -> QubitOperator:
        op = QubitOperator(())
        for gen, x_op in zip(self._generators, self._x_ops):
            op *= (2 ** (-0.5)) * (x_op + gen)
        return op

    def _block_diagnolize(self, op: QubitOperator) -> QubitOperator:
        transformed_op = (
            self._block_diagonalizing_clifford * op * self._block_diagonalizing_clifford
        )
        transformed_op.compress(self._tol)
        return transformed_op


def _get_z2_symmetries_generators(op: QubitOperator, n_qubits: int) -> np.ndarray:
    """
    Gets the Z2 symmetries generators of an operator.

    It can be shown that each vector in the kernel subspace of the operator's XZ matrix,
    after replacing Xs ans Zs, commutes with the operator.
    """
    xz_mat = qubit_op_to_xz_matrix(op, n_qubits)
    kernel = _get_kernel(xz_mat)
    return np.hstack((kernel[:, n_qubits:], kernel[:, :n_qubits]))


def _get_x_ops_for_generators(
    generators: np.ndarray, n_qubits: int
) -> list[QubitOperator]:
    """
    Tries to find single-qubit X operations for the given generators, such that each X
    operation anti-commutes with its matching generator and commutes with all the rest.
    """
    x_ops: list[QubitOperator] = []
    for row in range(len(generators)):

        # we look for a column in the Z-part of the matrix which is populated only with
        # 0s except for a 1 in the current generator: a X operation in this column's
        # qubit will anti-commute with the current generator and commute with all others
        found_col: Optional[int] = None
        for col in range(n_qubits):
            if (
                generators[row, n_qubits + col] == 1
                and np.all(generators[:row, n_qubits + col] == 0)
                and np.all(generators[row + 1 :, n_qubits + col] == 0)
            ):
                found_col = col
                break
        else:
            raise ClassiqValueError(
                "Failed to find X operator for the Z2 symmetry generator."
            )

        x_ops.append(QubitOperator(((found_col, "X"),)))

    return x_ops


def _get_sector_for_basis_state(
    generators_z_part: np.ndarray, state: list[bool]
) -> list[int]:
    """
    Computes the sector coefficients of a basis state by applying the generators.
    """
    sector: list[int] = []
    for gen in generators_z_part:
        coeff = 1
        for qubit in range(len(state)):
            if state[qubit] and gen[qubit] == 1:
                coeff *= -1
        sector.append(coeff)
    return sector


def _get_kernel(mat: np.ndarray) -> np.ndarray:
    """
    Computes the kernel subspace of the given Z2 matrix.

    Note: this function changes the given matrix inplace.
    """
    _transform_to_rref(mat)
    return _get_kernel_from_rref(mat)


def _transform_to_rref(mat: np.ndarray) -> None:
    """
    Transforms the given Z2 matrix into RREF (Reduced Row Echelon Form).

    Note: this function changes the given matrix inplace.
    """
    n_rows, n_cols = mat.shape
    col = 0

    for row in range(n_rows):
        while col < n_cols and mat[row, col] == 0:
            # find 1 in the current column and swap rows or move to the next column
            for krow in range(row + 1, n_rows):
                if mat[krow, col] == 1:
                    mat[[row, krow], col:] = mat[[krow, row], col:]
                    break
            else:
                col += 1

        if col < n_cols:
            # eliminate 1s in current column by XORing their rows with the current row
            curr_row = mat[row, col:]
            mat[:row, col:] ^= np.outer(mat[:row, col], curr_row)
            mat[row + 1 :, col:] ^= np.outer(mat[row + 1 :, col], curr_row)
            col += 1


def _get_kernel_from_rref(mat: np.ndarray) -> np.ndarray:
    """
    Computes the kernel subspace of the given Z2 matrix which is in RREF.
    """
    # remove all-zero rows
    mat = mat[~np.all(mat == 0, axis=1)]

    n_cols = mat.shape[1]

    # pivots are indices of columns with leading 1, free columns are the rest
    pivots = np.argmax(mat, axis=1)
    free_cols = np.setdiff1d(np.arange(n_cols), pivots)

    # for each free column we have a vector in the kernel with 1 in the free column
    # index and possibly 1s in pivots indices
    kernel = np.zeros((free_cols.size, n_cols), dtype=np.int8)
    for vec, free_col in zip(kernel, free_cols):
        vec[free_col] = 1

        for row, pivot in zip(mat, pivots):
            if row[free_col] == 1:
                vec[pivot] = 1

    return kernel


def _project_operator_to_subspace(
    op: QubitOperator, generators: Sequence[QubitOperator]
) -> QubitOperator:
    """
    Projects the given operator onto the symmetry subspace defined by the given
    generators.
    """
    projected_op = QubitOperator()
    for term, coeff in op.terms.items():
        single_term_op = QubitOperator(term, coeff)
        if all(
            commutator(single_term_op, gen) == QubitOperator() for gen in generators
        ):
            projected_op += single_term_op

    return projected_op
