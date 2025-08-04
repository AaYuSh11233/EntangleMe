import pydantic

from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import FunctionParams

RANDOMIZED_BENCHMARKING_INPUT: str = "TARGET"
RANDOMIZED_BENCHMARKING_OUTPUT: str = "TARGET"


class RandomizedBenchmarking(FunctionParams):
    num_of_qubits: pydantic.PositiveInt
    num_of_cliffords: pydantic.PositiveInt

    def _create_ios(self) -> None:
        self._inputs = {
            RANDOMIZED_BENCHMARKING_INPUT: RegisterArithmeticInfo(
                size=self.num_of_qubits
            )
        }
        self._outputs = {**self._inputs}
