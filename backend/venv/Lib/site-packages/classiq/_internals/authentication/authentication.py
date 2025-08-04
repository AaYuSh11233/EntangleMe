from classiq._internals import async_utils
from classiq._internals.client import client


def authenticate(overwrite: bool = False) -> None:
    """

    Authenticate to access the Classiq platform.

     Args:
        overwrite: A flag indicating whether to overwrite the existing
        authentication tokens. Defaults to `False`.

      If you are not registered, please visit the Classiq platform
    to complete registration: https://platform.classiq.io/
    """
    async_utils.run(authenticate_async(overwrite))


async def authenticate_async(overwrite: bool = False) -> None:
    """Async version of `register_device`"""
    await client().authenticate(overwrite)
