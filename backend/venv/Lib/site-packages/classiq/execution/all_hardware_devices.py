from classiq.interface.hardware import HardwareInformation

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper


def get_all_hardware_devices() -> list[HardwareInformation]:
    """
    Returns a list of all hardware devices known to Classiq.
    """
    return async_utils.run(ApiWrapper.call_get_all_hardware_devices())
