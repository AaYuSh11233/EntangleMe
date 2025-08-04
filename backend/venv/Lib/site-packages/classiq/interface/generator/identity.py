from typing import TYPE_CHECKING, Annotated

import pydantic
from pydantic import Field

from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import FunctionParams

if TYPE_CHECKING:
    NonEmptyRegisterUserInputList = list[RegisterUserInput]
else:
    NonEmptyRegisterUserInputList = Annotated[
        list[RegisterUserInput], Field(min_length=1)
    ]


class Identity(FunctionParams):
    arguments: NonEmptyRegisterUserInputList = pydantic.Field(
        description="registers describing the state (ordered)"
    )

    @pydantic.field_validator("arguments")
    @classmethod
    def _validate_argument_names(
        cls, arguments: list[RegisterUserInput]
    ) -> list[RegisterUserInput]:
        return [
            arg if arg.name else arg.revalued(name=cls._get_default_arg_name(index))
            for index, arg in enumerate(arguments)
        ]

    def _create_ios(self) -> None:
        self._inputs = {arg.name: arg for arg in self.arguments}
        self._outputs = {arg.name: arg for arg in self.arguments}

    @staticmethod
    def _get_default_arg_name(index: int) -> str:
        return f"arg_{index}"

    def get_power_order(self) -> int:
        return 1
