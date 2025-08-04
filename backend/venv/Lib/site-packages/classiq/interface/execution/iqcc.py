from typing import Optional

from pydantic import BaseModel, Field

from classiq.interface.helpers.versioned_model import VersionedModel


class IQCCInitAuthData(VersionedModel):
    auth_scope_id: str
    auth_method_id: str


class IQCCInitAuthResponse(VersionedModel):
    auth_url: str
    token_id: str


class IQCCProbeAuthData(IQCCInitAuthData):
    token_id: str


class IQCCProbeAuthResponse(VersionedModel):
    auth_token: str


class IQCCAuthItemDetails(BaseModel):
    id: str
    name: str
    description: str
    scope_id: Optional[str] = Field(default=None)


class IQCCAuthItemsDetails(VersionedModel):
    items: list[IQCCAuthItemDetails]


class IQCCListAuthMethods(VersionedModel):
    auth_scope_id: str


class IQCCListAuthTargets(VersionedModel):
    auth_scope_id: str
    auth_method_id: str
    auth_token: str
