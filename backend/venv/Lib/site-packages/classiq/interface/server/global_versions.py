from datetime import date
from typing import Any

from pydantic import BaseModel


class DeprecationInfo(BaseModel):
    deprecation_date: date
    removal_date: date


class GlobalVersions(BaseModel):
    deprecated: dict[str, DeprecationInfo]
    deployed: dict[str, Any]
