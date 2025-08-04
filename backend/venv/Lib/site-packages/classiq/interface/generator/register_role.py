from classiq.interface.enum_utils import StrEnum


class RegisterRole(StrEnum):
    INPUT = "input"
    OUTPUT = "output"
    AUXILIARY = "auxiliary"
    ZERO_INPUT = "zero_input"
    ZERO_OUTPUT = "zero_output"
    GARBAGE_OUTPUT = "garbage_output"
    EXPLICIT_ZERO_INPUT = "explicit_zero_input"

    @staticmethod
    def output_roles(include_garbage: bool = False) -> set["RegisterRole"]:
        roles = {
            RegisterRole.OUTPUT,
            RegisterRole.ZERO_OUTPUT,
            RegisterRole.AUXILIARY,
        }
        if include_garbage:
            roles.add(RegisterRole.GARBAGE_OUTPUT)
        return roles

    @staticmethod
    def input_roles() -> set["RegisterRole"]:
        return {
            RegisterRole.INPUT,
            RegisterRole.ZERO_INPUT,
            RegisterRole.AUXILIARY,
            RegisterRole.EXPLICIT_ZERO_INPUT,
        }

    @staticmethod
    def clean_output_roles() -> set["RegisterRole"]:
        return {RegisterRole.ZERO_OUTPUT, RegisterRole.AUXILIARY}

    @staticmethod
    def dirty_output_roles() -> set["RegisterRole"]:
        return {RegisterRole.OUTPUT, RegisterRole.GARBAGE_OUTPUT}
