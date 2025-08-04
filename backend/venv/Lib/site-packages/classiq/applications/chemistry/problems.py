from collections.abc import Sequence
from typing import Optional, cast

from openfermion import MolecularData
from openfermion.ops import FermionOperator
from openfermion.transforms import (
    get_fermion_operator,
    reorder,
)
from openfermion.utils import count_qubits

from classiq.interface.exceptions import ClassiqValueError


class FermionHamiltonianProblem:
    """
    Defines an electronic-structure problem using a Fermionic operator and electron count.
    Can also be constructed from a `MolecularData` object using the `from_molecule`
    method.

    Attributes:
        fermion_hamiltonian (FermionOperator): The fermionic hamiltonian of the problem.
            Assumed to be in the block-spin labeling.
        n_orbitals (int): Number of spatial orbitlas.
        n_alpha (int): Number of alpha particles.
        n_beta (int): Number of beta particles.
        n_particles (tuple[int, int]): Number of alpha and beta particles.
    """

    def __init__(
        self,
        fermion_hamiltonian: FermionOperator,
        n_particles: tuple[int, int],
        n_orbitals: Optional[int] = None,
    ) -> None:
        """
        Initializes a `FermionHamiltonianProblem` from the fermion hamiltonian, number
        of alpha and beta particles, and optionally the number of orbitals.

        Args:
            fermion_hamiltonian (FermionHamiltonianProblem): The fermionic hamiltonian
                of the problem. Assumed to be in the block-spin labeling.
            n_particles (tuple[int, int]): Number of alpha and beta particles.
            n_orbitals (int, optional): Number of spatial orbitals. If not specified,
                the number is inferred from `fermion_hamiltonian`.
        """
        self.fermion_hamiltonian = fermion_hamiltonian
        self.n_particles = n_particles
        self.n_alpha, self.n_beta = n_particles

        qubits = cast(int, count_qubits(fermion_hamiltonian))
        min_n_orbitals = (qubits + 1) // 2
        if n_orbitals is None:
            self.n_orbitals = min_n_orbitals
        else:
            if n_orbitals < min_n_orbitals:
                raise ClassiqValueError(
                    f"n_orbitals ({n_orbitals}) is less than the minimum number of orbitals {min_n_orbitals} inferred from the hamiltonian"
                )
            self.n_orbitals = n_orbitals

        if self.n_alpha > self.n_orbitals:
            raise ClassiqValueError(
                f"n_alpha ({self.n_alpha}) exceeds available orbitals ({self.n_orbitals})"
            )
        if self.n_beta > self.n_orbitals:
            raise ClassiqValueError(
                f"n_beta ({self.n_beta}) exceeds available orbitals ({self.n_orbitals})"
            )

    @property
    def occupied_alpha(self) -> list[int]:
        """
        Indices list of occupied alpha particles.
        """
        return list(range(self.n_alpha))

    @property
    def virtual_alpha(self) -> list[int]:
        """
        Indices list of virtual alpha particles.
        """
        return list(range(self.n_alpha, self.n_orbitals))

    @property
    def occupied_beta(self) -> list[int]:
        """
        Indices list of occupied beta particles.
        """
        return list(range(self.n_orbitals, self.n_orbitals + self.n_beta))

    @property
    def virtual_beta(self) -> list[int]:
        """
        Indices list of virtual beta particles.
        """
        return list(range(self.n_orbitals + self.n_beta, 2 * self.n_orbitals))

    @property
    def occupied(self) -> list[int]:
        """
        Indices list of occupied alpha and beta particles.
        """
        return self.occupied_alpha + self.occupied_beta

    @property
    def virtual(self) -> list[int]:
        """
        Indices list of virtual alpha and beta particles.
        """
        return self.virtual_alpha + self.virtual_beta

    @classmethod
    def from_molecule(
        cls,
        molecule: MolecularData,
        first_active_index: int = 0,
        remove_orbitlas: Optional[Sequence[int]] = None,
        op_compression_tol: float = 1e-13,
    ) -> "FermionHamiltonianProblem":
        """
        Constructs a `FermionHamiltonianProblem` from a molecule data.

        Args:
            molecule (MolecularData): The molecule data.
            first_active_index (int): The first active index, indicates all prior
                indices are freezed.
            remove_orbitlas (Sequence[int], optional): Active indices to be removed.
            op_compression_tol (float): Tolerance for trimming the fermion operator.

        Returns:
            The fermion hamiltonian problem.
        """
        if molecule.n_orbitals is None:
            raise ClassiqValueError(
                "The molecular data is not populated. Hint: call `run_pyscf` with the molecule."
            )

        if first_active_index >= molecule.n_orbitals:
            raise ClassiqValueError(
                f"Invalid active space: got first_active_index={first_active_index} "
                f", while the number of orbitals is {molecule.n_orbitals}."
                f" Active space must be non-empty."
            )

        freezed_indices = list(range(first_active_index))
        active_indices = list(range(first_active_index, molecule.n_orbitals))
        if remove_orbitlas:
            active_indices = list(set(active_indices) - set(remove_orbitlas))

        molecular_hamiltonian = molecule.get_molecular_hamiltonian(
            occupied_indices=freezed_indices,
            active_indices=active_indices,
        )

        n_freezed_orbitals = len(freezed_indices)
        n_orbitals = len(active_indices)
        n_alpha, n_beta = (
            molecule.get_n_alpha_electrons(),
            molecule.get_n_beta_electrons(),
        )
        n_particles = (n_alpha - n_freezed_orbitals, n_beta - n_freezed_orbitals)

        if n_orbitals <= 0 or min(n_particles) <= 0:
            raise ClassiqValueError(
                f"Degenerate active space: got {n_orbitals} spatial orbitals "
                f"and {n_particles} electrons. "
                f"This can happen if too many orbitals were frozen."
                f"Before freezing number of particle was ({n_alpha, n_beta})."
                f"Consider adjusting `first_active_index` or `remove_orbitlas` "
                f"to ensure the active space is non-empty."
            )

        fermion_op = get_fermion_operator(molecular_hamiltonian)
        # openfermion returns the operation in alternating-spin labeling, reorder to
        # keep the convention of block-spin labeling.
        fermion_op = _reorder_op_alternating_to_block(fermion_op)
        fermion_op.compress(abs_tol=op_compression_tol)

        return cls(
            fermion_hamiltonian=fermion_op,
            n_particles=n_particles,
            n_orbitals=n_orbitals,
        )


def _reorder_op_alternating_to_block(op: FermionOperator) -> FermionOperator:
    def _alternating_to_block(idx: int, num_modes: int) -> int:
        """Map an alternating-spin mode index to block-spin order."""
        n = num_modes // 2
        spin = idx % 2  # 0 = alpha, 1 = beta
        orbital = idx // 2
        return orbital + spin * n

    return reorder(op, _alternating_to_block)
