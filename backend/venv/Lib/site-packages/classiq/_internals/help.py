import webbrowser
from typing import Optional

from classiq.interface._version import SEMVER_VERSION

DOCS_BASE_URL = "https://docs.classiq.io/"


def open_help(version: Optional[str] = None) -> None:
    if version is None:
        version = SEMVER_VERSION
    if version == "0.0.0":
        # Dev Environment
        url_suffix = "latest/"
    else:
        url_suffix = "-".join(version.split(".")[:2]) + "/"
    webbrowser.open(DOCS_BASE_URL + url_suffix)
