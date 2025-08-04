from typing import TypeVar

import pydantic

Qubit = TypeVar("Qubit", bound=pydantic.NonNegativeInt)
Cycle = TypeVar("Cycle", bound=pydantic.NonNegativeInt)
Clbit = TypeVar("Clbit", bound=pydantic.NonNegativeInt)
