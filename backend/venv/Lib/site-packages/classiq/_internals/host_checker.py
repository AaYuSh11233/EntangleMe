from __future__ import annotations

import logging
import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import httpx
import pydantic
from packaging.version import Version
from pydantic import BaseModel

from classiq.interface.exceptions import ClassiqAPIError, ClassiqDeprecationWarning
from classiq.interface.interface_version import INTERFACE_VERSION
from classiq.interface.server.global_versions import DeprecationInfo, GlobalVersions

if TYPE_CHECKING:
    from classiq._internals.client import Client

_VERSION_UPDATE_SUGGESTION = 'Please run "pip install -U classiq" to upgrade the classiq SDK to the latest version.'
_logger = logging.getLogger(__name__)


class HostVersions(BaseModel):
    classiq_interface: pydantic.StrictStr = pydantic.Field()


class HostChecker:
    _UNKNOWN_VERSION = "0.0.0"

    def __init__(
        self,
        client: Client,
        client_version: str,
        interface_version: str = INTERFACE_VERSION,
    ) -> None:
        self._client = client
        self._client_version = client_version
        self._interface_version = interface_version

    def _get_interface_version(self) -> Optional[str]:
        global_interfaces = GlobalVersions.model_validate(
            self._client.sync_call_api(
                "get", "/interface_versions", use_versioned_url=False
            )
        )
        return global_interfaces.deployed.get(self._interface_version, None)

    def _get_host_version(self) -> str:
        host = HostVersions.model_validate(
            self._client.sync_call_api("get", "/versions")
        )
        return host.classiq_interface

    def _get_deprecation_info(self) -> Optional[DeprecationInfo]:
        global_versions = GlobalVersions.model_validate(
            self._client.sync_call_api("get", "/versions", use_versioned_url=False)
        )
        return global_versions.deprecated.get(self._client_version, None)

    @classmethod
    def _check_matching_versions(cls, lhs_version: str, rhs_version: str) -> bool:
        if lhs_version == cls._UNKNOWN_VERSION or rhs_version == cls._UNKNOWN_VERSION:
            # In case one of those versions is unknown, they are considered equal
            _logger.debug(
                "Either %s or %s is an unknown version. Assuming both versions are equal.",
                lhs_version,
                rhs_version,
            )
            return True
        processed_lhs = Version(lhs_version)
        processed_rhs = Version(rhs_version)
        return processed_lhs.release[:2] == processed_rhs.release[:2]

    def check_host_version(self) -> None:
        try:
            interface_version = self._get_interface_version()
        except httpx.ConnectError:
            _logger.warning(
                "Version check failed - host unavailable.",
            )
        else:
            if interface_version is None:
                raise ClassiqAPIError(
                    f"You are using an unsupported version of Classiq SDK - {self._client_version}. "
                    f"{_VERSION_UPDATE_SUGGESTION}"
                )

    def check_deprecated_version(self) -> None:
        try:
            deprecation_info = self._get_deprecation_info()
        except httpx.ConnectError:
            _logger.warning(
                "Deprecation check failed - host unavailable.",
            )
        else:
            if deprecation_info is None:
                return
            removal_date = (
                deprecation_info.removal_date.date()
                if isinstance(deprecation_info.removal_date, datetime)
                else deprecation_info.removal_date
            )
            warnings.warn(
                f"The current version of 'classiq' has been deprecated, and"
                f" will not be supported as of {removal_date}. "
                f"{_VERSION_UPDATE_SUGGESTION}",
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
