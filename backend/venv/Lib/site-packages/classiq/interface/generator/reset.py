from classiq.interface.generator.arith.register_user_input import (
    RegisterArithmeticInfo,
    RegisterUserInput,
)
from classiq.interface.generator.function_params import FunctionParams


class Reset(FunctionParams):
    target: RegisterUserInput

    def _create_ios(self) -> None:
        mapping: dict[str, RegisterArithmeticInfo] = {self.target.name: self.target}
        self._inputs = mapping
        self._outputs = mapping
