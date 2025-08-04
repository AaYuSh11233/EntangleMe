from typing import TYPE_CHECKING, Annotated, Any

import pydantic
from pydantic import Field, StrictStr, StringConstraints

from classiq.interface.generator.arith.number_utils import MAXIMAL_MACHINE_PRECISION
from classiq.interface.generator.parameters import ParameterComplexType

# General int types

MAX_EXPRESSION_SIZE = 32768

if TYPE_CHECKING:
    PydanticLargerThanOneInteger = int
    PydanticMachinePrecision = int
else:
    PydanticLargerThanOneInteger = Annotated[int, Field(gt=1)]

    PydanticMachinePrecision = Annotated[int, Field(gt=0, le=MAXIMAL_MACHINE_PRECISION)]


# Probability float types
if TYPE_CHECKING:
    PydanticProbabilityFloat = float
    PydanticNonOneProbabilityFloat = float
    PydanticNonZeroProbabilityFloat = float
else:
    PydanticProbabilityFloat = Annotated[float, Field(ge=0.0, le=1.0)]

    PydanticNonOneProbabilityFloat = Annotated[float, Field(ge=0.0, lt=1.0)]

    PydanticNonZeroProbabilityFloat = Annotated[float, Field(gt=0.0, le=1.0)]


# CVAR parameter types
if TYPE_CHECKING:
    PydanticAlphaParamCVAR = float
else:
    PydanticAlphaParamCVAR = Annotated[float, Field(gt=0.0, le=1.0)]


# General string types
if TYPE_CHECKING:
    PydanticNonEmptyString = str
else:
    PydanticNonEmptyString = Annotated[str, Field(min_length=1)]

# Name string types
if TYPE_CHECKING:
    PydanticFunctionNameStr = str
else:
    PydanticFunctionNameStr = Annotated[
        str, Field(strict=True, pattern="^([A-Za-z][A-Za-z0-9_]*)$")
    ]

if TYPE_CHECKING:
    PydanticPauliMonomial = tuple
else:
    PydanticPauliMonomial = Annotated[list[Any], Field(min_length=2, max_length=2)]

if TYPE_CHECKING:
    PydanticPauliMonomialStr = str
else:
    PydanticPauliMonomialStr = Annotated[
        StrictStr,
        StringConstraints(strip_whitespace=True, min_length=1, pattern="^[IXYZ]+$"),
    ]

PauliTuple = tuple[PydanticPauliMonomialStr, ParameterComplexType]
PydanticPauliList = Annotated[list[PauliTuple], Field(min_length=1)]

if TYPE_CHECKING:
    PydanticFloatTuple = tuple[float, float]
else:
    PydanticFloatTuple = Annotated[list[float], Field(min_length=2, max_length=2)]

PydanticNonNegIntTuple = Annotated[
    list[pydantic.NonNegativeInt], Field(min_length=2, max_length=2)
]

if TYPE_CHECKING:
    PydanticExpressionStr = str
else:
    PydanticExpressionStr = Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MAX_EXPRESSION_SIZE
        ),
    ]
if TYPE_CHECKING:
    AtomType = tuple[str, list[float]]
else:
    AtomType = Annotated[list[Any], Field(min_length=2, max_length=2)]


if TYPE_CHECKING:
    PydanticDataDogUuid = str
else:
    PydanticDataDogUuid = Annotated[
        str,
        Field(
            pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
        ),
    ]

if TYPE_CHECKING:
    PydanticDataDogGo = int
else:
    PydanticDataDogGo = Annotated[int, Field(ge=0)]
