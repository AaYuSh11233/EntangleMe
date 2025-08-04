import time
import webbrowser

from classiq.interface.exceptions import ClassiqError
from classiq.interface.execution.iqcc import (
    IQCCAuthItemDetails,
    IQCCInitAuthData,
    IQCCListAuthMethods,
    IQCCListAuthTargets,
    IQCCProbeAuthData,
)

from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.async_utils import syncify_function


async def list_iqcc_auth_scopes_async() -> list[IQCCAuthItemDetails]:
    """List available authentication scopes in IQCC Bounday.

    Returns:
        The available authentication scopes.
    """
    response = await ApiWrapper().call_iqcc_list_auth_scopes()
    return response.items


list_iqcc_auth_scopes = syncify_function(list_iqcc_auth_scopes_async)


async def list_iqcc_auth_methods_async(auth_scope_id: str) -> list[IQCCAuthItemDetails]:
    """List available authentication methods in IQCC Bounday for a specific scope.

    Args:
        auth_scope_id: The ID of the IQCC Boundary authentication scope.

    Returns:
        The available authentication methods.
    """
    response = await ApiWrapper().call_iqcc_list_auth_methods(
        IQCCListAuthMethods(auth_scope_id=auth_scope_id)
    )
    return response.items


list_iqcc_auth_methods = syncify_function(list_iqcc_auth_methods_async)


async def generate_iqcc_token_async(
    auth_scope_id: str,
    auth_method_id: str,
    timeout: float = 120,
    probe_interval: float = 1,
    print_auth_url: bool = True,
) -> str:
    """Interactively generate a token for use in IQCC backends.

    Args:
        auth_scope_id: The ID of the IQCC Boundary authentication scope.
        auth_method_id: The ID of the IQCC Boundary authentication method.
        timeout: Number of seconds to wait for the interactive authentication to complete.
        probe_interval: Number of seconds to wait between probes of the authentication.
        print_auth_url: Whether to print the authentication URL, useful for headless machines with no browser.

    Returns:
        The authentication token string to use directly in `IQCCBackendPreferences`.

    Raises:
        ClassiqError: In case timeout has reached before a successful authentication.
    """
    initiate_response = await ApiWrapper().call_iqcc_init_auth(
        IQCCInitAuthData(auth_scope_id=auth_scope_id, auth_method_id=auth_method_id)
    )

    if print_auth_url:
        print("Please proceed with authentication on your web browser.")  # noqa: T201
        print("If no window has opened, use this link to authenticate:")  # noqa: T201
        print(initiate_response.auth_url)  # noqa: T201

    webbrowser.open_new_tab(initiate_response.auth_url)

    start_time = time.monotonic()
    while True:
        time.sleep(probe_interval)
        probe_response = await ApiWrapper().call_iqcc_probe_auth(
            IQCCProbeAuthData(
                auth_scope_id=auth_scope_id,
                auth_method_id=auth_method_id,
                token_id=initiate_response.token_id,
            )
        )
        if probe_response is not None:
            return probe_response.auth_token

        if time.monotonic() - start_time > timeout:
            raise ClassiqError(
                f"Timeout has reached while probing IQCC authentication. Please try again and make sure to authenticate within {timeout} seconds, or increase the timeout."
            )


generate_iqcc_token = syncify_function(generate_iqcc_token_async)


async def list_iqcc_auth_targets_async(
    auth_scope_id: str,
    auth_method_id: str,
    auth_token: str,
) -> list[IQCCAuthItemDetails]:
    """List available authentication targets in IQCC Boundary for the user.

    Args:
        auth_scope_id: The ID of the IQCC Boundary authentication scope.
        auth_method_id: The ID of the IQCC Boundary authentication method.
        auth_token: The authentication token string returned from `generate_iqcc_token_async`.

    Returns:
        The available authentication targets.
    """
    response = await ApiWrapper().call_iqcc_list_auth_targets(
        IQCCListAuthTargets(
            auth_scope_id=auth_scope_id,
            auth_method_id=auth_method_id,
            auth_token=auth_token,
        )
    )
    return response.items


list_iqcc_auth_target = syncify_function(list_iqcc_auth_targets_async)
