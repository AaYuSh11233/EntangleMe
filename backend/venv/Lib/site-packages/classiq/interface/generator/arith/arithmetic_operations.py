import abc
from collections.abc import Iterable
from typing import ClassVar, Final, Optional

import pydantic

from classiq.interface.generator.arith.machine_precision import (
    DEFAULT_MACHINE_PRECISION,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import FunctionParams

IMPLICIT_OUTPUTS: Final[str] = "implicit_outputs"
DEFAULT_GARBAGE_OUT_NAME: Final[str] = "extra_qubits"
MODULO_WITH_FRACTION_PLACES_ERROR_MSG: Final[str] = (
    "Modulo with fraction places not supported"
)


class ArithmeticOperationParams(FunctionParams):
    output_size: Optional[pydantic.PositiveInt] = pydantic.Field(default=None)
    machine_precision: pydantic.PositiveInt = DEFAULT_MACHINE_PRECISION
    output_name: ClassVar[str]
    garbage_output_name: ClassVar[str] = DEFAULT_GARBAGE_OUT_NAME
    _result_register: Optional[RegisterArithmeticInfo] = pydantic.PrivateAttr(
        default=None
    )

    @abc.abstractmethod
    def _get_result_register(self) -> RegisterArithmeticInfo:
        pass

    @property
    def result_register(self) -> RegisterArithmeticInfo:
        if self._result_register is None:
            self._result_register = self._get_result_register()
        return self._result_register

    @abc.abstractmethod
    def is_inplaced(self) -> bool:
        pass

    @property
    def _include_sign(self) -> bool:
        return self.output_size is None

    def _legal_bounds(
        self, suggested_bounds: tuple[float, float], max_bounds: tuple[float, float]
    ) -> Optional[tuple[float, float]]:
        if self.output_size is None or (
            suggested_bounds[0] >= max_bounds[0]
            and suggested_bounds[1] <= max_bounds[1]
        ):
            return suggested_bounds
        return None

    @abc.abstractmethod
    def get_params_inplace_options(self) -> Iterable["ArithmeticOperationParams"]:
        pass
