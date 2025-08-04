from typing import Literal, Union

import pydantic
from pydantic import ConfigDict

from classiq.interface.chemistry.elements import ELEMENTS
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.custom_pydantic_types import AtomType
from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)


class Atom(HashablePydanticBaseModel):
    symbol: Literal[tuple(ELEMENTS)] = pydantic.Field(description="The atom symbol")  # type: ignore[valid-type]
    x: float = pydantic.Field(description="The x coordinate of the atom")
    y: float = pydantic.Field(description="The y coordinate of the atom")
    z: float = pydantic.Field(description="The z coordinate of the atom")


class Molecule(HashablePydanticBaseModel):
    atoms: list[Atom] = pydantic.Field(
        description="A list of atoms each containing the atoms symbol and  its (x,y,z) location",
        min_length=1,
    )
    spin: pydantic.NonNegativeInt = pydantic.Field(
        default=1, description="spin of the molecule"
    )
    charge: pydantic.NonNegativeInt = pydantic.Field(
        default=0, description="charge of the molecule"
    )

    @property
    def atoms_type(self) -> list[AtomType]:
        return [(atom.symbol, [atom.x, atom.y, atom.z]) for atom in self.atoms]

    @classmethod
    def _validate_atom(cls, atom: Union[AtomType, Atom]) -> Atom:
        if isinstance(atom, (list, tuple)):
            return cls._validate_old_atoms_type(atom)
        return atom

    @pydantic.field_validator("atoms", mode="before")
    @classmethod
    def _validate_atoms(cls, atoms: list[Union[AtomType, Atom]]) -> list[Atom]:
        return [cls._validate_atom(atom) for atom in atoms]

    @staticmethod
    def _validate_old_atoms_type(atom: AtomType) -> Atom:
        if len(atom) != 2:
            raise ClassiqValueError(
                "each atom should be a list of two entries: 1) name pf the elemnt (str) 2) list of its (x,y,z) location"
            )
        if not isinstance(atom[0], str):
            raise ClassiqValueError(
                f"atom name should be a string. unknown element: {atom[0]}."
            )
        if len(atom[1]) != 3:
            raise ClassiqValueError(
                f"location of the atom is of length three, representing the (x,y,z) coordinates of the atom, error value: {atom[1]}"
            )
        for idx in atom[1]:
            if not isinstance(idx, (float, int)):
                raise ClassiqValueError(
                    f"coordinates of the atom should be of type float. error value: {idx}"
                )
        symbol, coordinate = atom

        return Atom(symbol=symbol, x=coordinate[0], y=coordinate[1], z=coordinate[2])

    model_config = ConfigDict(frozen=True)
