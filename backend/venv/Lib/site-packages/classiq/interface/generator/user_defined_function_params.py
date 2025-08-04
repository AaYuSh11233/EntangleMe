from collections.abc import Mapping

import pydantic
from pydantic import ConfigDict

from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import ArithmeticIODict, FunctionParams


class CustomFunction(FunctionParams):
    """
    A user-defined custom function parameters object.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    _name: str = pydantic.PrivateAttr(default="")

    input_decls: ArithmeticIODict = pydantic.Field(
        default_factory=dict,
        description="A mapping from the inputs names to the registers information. should be identical to the register defined in the function creation.",
    )

    output_decls: ArithmeticIODict = pydantic.Field(
        default_factory=dict,
        description="A mapping from the outputs names to the registers information. should be identical to the register defined in the function creation.",
    )

    def _create_ios(self) -> None:
        self._inputs = self.input_decls
        self._outputs = self.output_decls

    def generate_ios(
        self,
        inputs: Mapping[str, RegisterArithmeticInfo],
        outputs: Mapping[str, RegisterArithmeticInfo],
    ) -> None:
        self._inputs = dict(inputs)
        self._outputs = dict(outputs)

    @property
    def name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        self._name = name

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name))
