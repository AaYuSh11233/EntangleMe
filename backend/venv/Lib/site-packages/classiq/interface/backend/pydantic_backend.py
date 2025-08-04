from typing import TYPE_CHECKING, Annotated

from pydantic import Field, StrictStr, constr

AZURE_QUANTUM_RESOURCE_ID_REGEX = r"^/subscriptions/([a-fA-F0-9-]*)/resourceGroups/([^\s/]*)/providers/Microsoft\.Quantum/Workspaces/([^\s/]*)$"

_IONQ_API_KEY_LENGTH: int = 32
_ALICE_BOB_API_KEY_LENGTH: int = 72
INVALID_API_KEY: str = _IONQ_API_KEY_LENGTH * "a"
INVALID_EMAIL_OQC: str = "aa@aa.aa"
INVALID_PASSWORD_OQC: str = "Aa1!Aa1!"  # noqa: S105

EXECUTION_PARAMETER_PATTERN = "[_a-z][_a-z0-9]*"

if TYPE_CHECKING:
    PydanticAwsRoleArn = str
    PydanticS3BucketKey = str
    PydanticS3BucketName = str
    PydanticAzureResourceIDType = str
    PydanticIonQApiKeyType = str
    PydanticArgumentNameType = str
    PydanticExecutionParameter = str
    PydanticAliceBobApiKeyType = str
else:
    # TODO Simplify regular expressions in this file

    PydanticAwsRoleArn = Annotated[
        StrictStr,
        constr(
            strip_whitespace=True,
        ),
    ]

    PydanticS3BucketKey = Annotated[
        StrictStr, constr(strip_whitespace=True, min_length=1)
    ]

    PydanticAzureResourceIDType = Annotated[
        str, Field(pattern=AZURE_QUANTUM_RESOURCE_ID_REGEX)
    ]

    PydanticIonQApiKeyType = Annotated[
        str, Field(pattern=f"[A-Za-z0-9]{{{_IONQ_API_KEY_LENGTH}}}")
    ]

    PydanticAliceBobApiKeyType = Annotated[
        StrictStr, constr(min_length=1, strip_whitespace=True)
    ]

    PydanticArgumentNameType = Annotated[str, Field(pattern="[_a-zA-Z][_a-zA-Z0-9]*")]

    PydanticExecutionParameter = Annotated[
        str, Field(pattern=EXECUTION_PARAMETER_PATTERN)
    ]
