from typing import Any

import pydantic

from classiq.interface._version import VERSION
from classiq.interface.interface_version import INTERFACE_VERSION


class VersionedModel(pydantic.BaseModel):
    version: str = pydantic.Field(default=VERSION)
    interface_version: str = pydantic.Field(default="0")

    @pydantic.model_validator(mode="before")
    @classmethod
    def set_interface_version(cls, values: dict[str, Any]) -> dict[str, Any]:
        # We "override" the default value mechanism so that the schema does not depend on the version
        if "interface_version" not in values:
            values["interface_version"] = INTERFACE_VERSION
        return values
