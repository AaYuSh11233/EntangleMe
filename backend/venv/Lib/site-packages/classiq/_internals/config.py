"""Configuration of the SDK module."""

import os
import pathlib
from typing import Optional, Union

import configargparse  # type: ignore[import]
import pydantic
from pydantic import BaseModel

from classiq.interface.enum_utils import StrEnum
from classiq.interface.server.routes import DEFAULT_IDE_FE_APP

DEFAULT_HOST = "https://api.classiq.io"


class SDKMode(StrEnum):
    DEV = "dev"
    PROD = "prod"


class Configuration(BaseModel):
    """Object containing configuration options (see description in fields)."""

    host: pydantic.AnyHttpUrl = pydantic.Field(..., description="Classiq backend URI.")
    ide: pydantic.AnyHttpUrl = pydantic.Field(
        default=DEFAULT_IDE_FE_APP, description="Classiq IDE URI."
    )
    should_check_host: bool = pydantic.Field(
        default=True, description="Should check backend URI and version."
    )
    mode: SDKMode = pydantic.Field(
        default=SDKMode.PROD, description="The operational mode of the SDK"
    )
    text_only: bool = pydantic.Field(
        default=False, description="Should classiq avoid relying on GUI"
    )


_DEFAULT_CONFIG_FILES = [str(pathlib.Path("classiq", "config.ini"))]
if os.name == "posix":
    # Unix convensions:
    #   System-wide configuration rests in "/etc"
    #       either as "/etc/program_name.conf" or as "/etc/program_name/some_name"
    #   User-wide configuration rests in "~/.config"
    # Order matters - System-wide is most general, than user-wide,
    #   and than folder-specific configration
    _DEFAULT_CONFIG_FILES = [
        "/etc/classiq/config.ini",
        "/etc/classiq.conf",
        "~/.config/classiq/config.ini",
        "~/.config/classiq.conf",
    ] + _DEFAULT_CONFIG_FILES


def init(args: Optional[Union[str, list[str]]] = None) -> Configuration:
    """Initialize the configuration object.

    Args:
        args (): Non-default arguments.

    Returns:
        Initialized configuration object.
    """
    arg_parser = configargparse.ArgParser(default_config_files=_DEFAULT_CONFIG_FILES)

    arg_parser.add_argument(
        "--classiq-config-file",
        is_config_file=True,
        help="Configuration file path",
        env_var="CLASSIQ_CONFIG_FILE",
    )
    arg_parser.add_argument(
        "--classiq-host",
        help="The URL of Classiq's backend host",
        env_var="CLASSIQ_HOST",
        default=DEFAULT_HOST,
    )
    arg_parser.add_argument(
        "--classiq-ide",
        help="The URL of Classiq's engine host",
        env_var="CLASSIQ_IDE",
        default=DEFAULT_IDE_FE_APP,
    )
    arg_parser.add_argument(
        "--classiq-skip-check-host",
        dest="classiq_skip_check_host",
        help="Should skip classiq host and version",
        env_var="CLASSIQ_SKIP_CHECK_HOST",
        action="store_true",
    )
    arg_parser.add_argument(
        "--classiq-mode",
        dest="classiq_mode",
        help="Classiq SDK mode",
        env_var="CLASSIQ_SDK_MODE",
        type=SDKMode,
        default=SDKMode.PROD,
    )
    arg_parser.add_argument(
        "--text-only",
        dest="classiq_text_only",
        help="Should classiq avoid relying on GUI",
        env_var="CLASSIQ_TEXT_ONLY",
        action="store_true",
    )

    parsed_args, _ = arg_parser.parse_known_args(args=args)
    return Configuration(
        host=parsed_args.classiq_host,
        ide=parsed_args.classiq_ide,
        should_check_host=not parsed_args.classiq_skip_check_host,
        mode=parsed_args.classiq_mode,
        text_only=parsed_args.classiq_text_only,
    )
