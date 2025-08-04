from collections.abc import Iterable
from typing import Optional

import pydantic
from pydantic import ConfigDict

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.argument_utils import RegisterOrConst
from classiq.interface.generator.arith.arithmetic_operations import (
    ArithmeticOperationParams,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import get_zero_input_name


def get_arg_name(idx: int) -> str:
    return f"arg_{idx}"


class LogicalOps(ArithmeticOperationParams):
    args: list[RegisterOrConst]
    target: Optional[RegisterArithmeticInfo]
    _should_invert_node_list: list[str] = pydantic.PrivateAttr(default_factory=list)

    def update_should_invert_node_list(self, invert_args: list[str]) -> None:
        self._should_invert_node_list.extend(invert_args)

    @pydantic.field_validator("output_size")
    @classmethod
    def _validate_output_size(cls, output_size: Optional[int]) -> int:
        if output_size is not None and output_size != 1:
            raise ClassiqValueError("logical operation output size must be 1")
        return 1

    @pydantic.field_validator("args")
    @classmethod
    def _validate_inputs_sizes(
        cls, arguments: list[RegisterOrConst]
    ) -> list[RegisterOrConst]:
        for arg_idx, arg in enumerate(arguments):
            if isinstance(arg, RegisterArithmeticInfo) and not arg.is_boolean_register:
                raise ClassiqValueError(
                    f"All inputs to logical and must be of size 1 (at argument #{arg_idx})"
                )
        return arguments

    def _get_result_register(self) -> RegisterArithmeticInfo:
        return RegisterArithmeticInfo(size=1)

    def _create_ios(self) -> None:
        args = {
            get_arg_name(idx): arg
            for idx, arg in enumerate(self.args)
            if isinstance(arg, RegisterArithmeticInfo)
        }
        self._inputs = {**args}
        self._outputs = {**args, self.output_name: self.result_register}
        if self.target:
            self._inputs[self.output_name] = self.target
        else:
            self._create_zero_input_registers(
                {get_zero_input_name(self.output_name): self.result_register.size}
            )

    def is_inplaced(self) -> bool:
        return False

    def get_params_inplace_options(self) -> Iterable["LogicalOps"]:
        return ()

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LogicalAnd(LogicalOps):
    output_name = "and"
    pass


class LogicalOr(LogicalOps):
    output_name = "or"
    pass
