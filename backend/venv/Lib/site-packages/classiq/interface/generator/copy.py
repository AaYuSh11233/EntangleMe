from typing import Optional

import pydantic

from classiq.interface.generator.arith import argument_utils
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import FunctionParams


class Copy(FunctionParams):
    source: argument_utils.RegisterOrConst
    target: RegisterArithmeticInfo
    output_size: Optional[pydantic.PositiveInt] = pydantic.Field(default=None)

    @property
    def source_size(self) -> int:
        return argument_utils.size(self.source)

    @property
    def source_reg_size(self) -> int:
        return (
            self.source.size if isinstance(self.source, RegisterArithmeticInfo) else 0
        )

    @property
    def source_fraction_places(self) -> int:
        return argument_utils.fraction_places(self.source)

    @property
    def offset(self) -> int:
        return self.target.fraction_places - self.source_fraction_places

    @property
    def source_name(self) -> str:
        return "source"

    @property
    def target_name(self) -> str:
        return "target"

    def _create_ios(self) -> None:
        self._inputs = {
            self.target_name: self.target,
        }
        if isinstance(self.source, RegisterArithmeticInfo):
            self._inputs[self.source_name] = self.source
        self._outputs = {**self._inputs}
