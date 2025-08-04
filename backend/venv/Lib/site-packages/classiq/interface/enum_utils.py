import sys

if sys.version_info[:2] >= (3, 11):
    # breaking change introduced in python 3.11
    from enum import ReprEnum, StrEnum
else:
    from enum import Enum  # pragma: no cover

    class StrEnum(str, Enum):  # pragma: no cover
        pass  # pragma: no cover

    ReprEnum = Enum  # pragma: no cover
