from collections.abc import Iterable
from typing import Optional

import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.chemistry_function_params import (
    ChemistryFunctionParams,
)
from classiq.interface.generator.excitations import (
    EXCITATIONS_TYPE,
    EXCITATIONS_TYPE_EXACT,
)

_EXCITATIONS_DICT = {"s": 1, "d": 2, "t": 3, "q": 4}

DEFAULT_EXCITATIONS = [1, 2]


def default_excitation_factory() -> EXCITATIONS_TYPE_EXACT:
    return DEFAULT_EXCITATIONS


class UCC(ChemistryFunctionParams):
    """
    Ucc ansatz
    """

    use_naive_evolution: bool = pydantic.Field(
        default=False, description="Whether to evolve the operator naively"
    )
    excitations: EXCITATIONS_TYPE = pydantic.Field(
        default_factory=default_excitation_factory,
        description="type of excitation operators in the UCC ansatz",
    )
    max_depth: Optional[pydantic.PositiveInt] = pydantic.Field(
        default=None,
        description="Maximum depth of the generated quantum circuit ansatz",
    )
    parameter_prefix: str = pydantic.Field(
        default="ucc_param_",
        description="Prefix for the generated parameters",
    )

    @pydantic.field_validator("excitations")
    @classmethod
    def _validate_excitations(cls, excitations: EXCITATIONS_TYPE) -> EXCITATIONS_TYPE:
        if isinstance(excitations, int):
            if excitations not in _EXCITATIONS_DICT.values():
                raise ClassiqValueError(
                    f"possible values of excitations are {list(_EXCITATIONS_DICT.values())}"
                )
            excitations = [excitations]

        elif isinstance(excitations, Iterable):
            excitations = list(excitations)  # type: ignore[assignment]
            if all(isinstance(idx, int) for idx in excitations):
                if any(idx not in _EXCITATIONS_DICT.values() for idx in excitations):
                    raise ClassiqValueError(
                        f"possible values of excitations are {list(_EXCITATIONS_DICT.values())}"
                    )

            elif all(isinstance(idx, str) for idx in excitations):
                if any(idx not in _EXCITATIONS_DICT.keys() for idx in excitations):
                    raise ClassiqValueError(
                        f"possible values of excitations are {list(_EXCITATIONS_DICT.keys())}"
                    )
                excitations = sorted(_EXCITATIONS_DICT[idx] for idx in excitations)  # type: ignore[index]

            else:
                raise ClassiqValueError(
                    "excitations must be of the same type (all str or all int)"
                )
        return excitations
