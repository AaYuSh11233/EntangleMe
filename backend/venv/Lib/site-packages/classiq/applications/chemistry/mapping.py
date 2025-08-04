from typing import Any, NoReturn

from openfermion.ops import FermionOperator, QubitOperator
from openfermion.transforms import (
    bravyi_kitaev,
    jordan_wigner,
)

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError

from classiq.applications.chemistry.problems import FermionHamiltonianProblem


class MappingMethod(StrEnum):
    """
    Mapping methods from fermionic operators to qubits operators.
    """

    JORDAN_WIGNER = "jw"
    BRAVYI_KITAEV = "bk"


class FermionToQubitMapper:
    """
    Mapper between fermionic operators to qubits operators, using one of the supported
    mapping methods (see `MappingMethod`).

    Attributes:
        method (MappingMethod): The mapping method.
    """

    def __init__(
        self,
        method: MappingMethod = MappingMethod.JORDAN_WIGNER,
    ) -> None:
        """
        Initializes a `FermionToQubitMapper` object using the specified method.

        Args:
            method (MappingMethod): The mapping method.
        """
        self.method = method

        if self.method is MappingMethod.JORDAN_WIGNER:
            self._mapper = jordan_wigner
        elif self.method is MappingMethod.BRAVYI_KITAEV:
            self._mapper = bravyi_kitaev
        else:
            _raise_invalid_method(method)

    def map(
        self, fermion_op: FermionOperator, *args: Any, **kwargs: Any
    ) -> QubitOperator:
        """
        Maps the given fermionic operator to a qubits operator using the mapper's
        configuration.

        Args:
            fermion_op (FermionOperator): A fermionic operator.
            *args: Extra parameters which are ignored, may be used in subclasses.
            **kwargs: Extra parameters which are ignored, may be used in subclasses.

        Returns:
            The mapped qubits operator.
        """
        return self._mapper(fermion_op)

    def get_num_qubits(self, problem: FermionHamiltonianProblem) -> int:
        """
        Gets the number of qubits after mapping the given problem into qubits space.

        Args:
            problem (FermionHamiltonianProblem): The fermion problem.

        Returns:
            The number of qubits.
        """
        return 2 * problem.n_orbitals


# statically validate that we have exhaustively searched all methods by defining its type
# as `NoReturn`, while dynamically raising an indicative error
def _raise_invalid_method(method: NoReturn) -> NoReturn:
    raise ClassiqValueError(f"Invalid mapping method: {method}")
