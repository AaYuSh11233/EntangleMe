from typing import Annotated, Literal, Optional, Union, cast

import pydantic
from pydantic import ConfigDict, Field
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.chemistry.fermionic_operator import SummedFermionicOperator
from classiq.interface.chemistry.molecule import Molecule
from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)

"""
The correct type hint is:
NumSpinUpParticles = pydantic.NonNegativeInt
NumSpinDownParticles = pydantic.NonNegativeInt
NumParticles = Tuple[NumSpinUpParticles, NumSpinDownParticles]

But:
A) the NonNegativeInt makes the ts-schemas have a `Minimum` object,
    which is undefined, thus causing an error
B) a tuple of a specific size gives another, different error

Thus, we use `int` and manually check its value
And use a list, and manually check its length
"""
NumSpinUpParticles = pydantic.NonNegativeInt
NumSpinDownParticles = pydantic.NonNegativeInt
NumParticles = tuple[NumSpinUpParticles, NumSpinDownParticles]


class FermionMapping(StrEnum):
    JORDAN_WIGNER = "jordan_wigner"
    PARITY = "parity"
    BRAVYI_KITAEV = "bravyi_kitaev"
    FAST_BRAVYI_KITAEV = "fast_bravyi_kitaev"


class GroundStateProblem(HashablePydanticBaseModel):
    kind: str

    mapping: FermionMapping = pydantic.Field(
        default=FermionMapping.JORDAN_WIGNER,
        description="Fermionic mapping type",
        title="Fermion Mapping",
    )
    z2_symmetries: bool = pydantic.Field(
        default=False,
        description="whether to perform z2 symmetries reduction",
    )
    num_qubits: Optional[int] = pydantic.Field(default=None)

    @pydantic.field_validator("z2_symmetries")
    @classmethod
    def _validate_z2_symmetries(cls, z2_symmetries: bool, info: ValidationInfo) -> bool:
        if (
            z2_symmetries
            and info.data.get("mapping") == FermionMapping.FAST_BRAVYI_KITAEV
        ):
            raise ClassiqValueError(
                "z2 symmetries reduction can not be used for fast_bravyi_kitaev mapping"
            )
        return z2_symmetries

    model_config = ConfigDict(frozen=True)


class MoleculeProblem(GroundStateProblem):
    kind: Literal["molecule"] = pydantic.Field(default="molecule")

    molecule: Molecule
    basis: str = pydantic.Field(default="sto3g", description="Molecular basis set")
    freeze_core: bool = pydantic.Field(default=False)
    remove_orbitals: list[int] = pydantic.Field(
        default_factory=list, description="list of orbitals to remove"
    )


class HamiltonianProblem(GroundStateProblem):
    kind: Literal["hamiltonian"] = pydantic.Field(default="hamiltonian")

    hamiltonian: SummedFermionicOperator = pydantic.Field(
        description="Hamiltonian as a fermionic operator"
    )
    num_particles: list[pydantic.PositiveInt] = pydantic.Field(
        description="Tuple containing the numbers of alpha particles and beta particles"
    )

    @pydantic.field_validator("num_particles", mode="before")
    @classmethod
    def _validate_num_particles(
        cls,
        num_particles: Union[
            list[Union[int, float]], tuple[Union[int, float], Union[int, float]]
        ],
    ) -> list[int]:
        assert isinstance(num_particles, (list, tuple))
        assert len(num_particles) == 2

        num_particles = [int(x) for x in num_particles]

        assert num_particles[0] >= 1
        assert num_particles[1] >= 1

        return cast(list[int], num_particles)


CHEMISTRY_PROBLEMS = (MoleculeProblem, HamiltonianProblem)
CHEMISTRY_PROBLEMS_TYPE = Annotated[
    Union[MoleculeProblem, HamiltonianProblem],
    Field(
        discriminator="kind",
        description="Ground state problem object describing the system.",
    ),
]
CHEMISTRY_ANSATZ_NAMES = ["hw_efficient", "ucc", "hva"]
