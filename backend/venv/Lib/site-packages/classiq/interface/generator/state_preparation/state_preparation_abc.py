import abc

from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
    FunctionParams,
)


class StatePreparationABC(FunctionParams, abc.ABC):
    @property
    @abc.abstractmethod
    def num_state_qubits(self) -> int:
        pass

    def _create_ios(self) -> None:
        self._inputs = dict()
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(
                name=DEFAULT_OUTPUT_NAME, size=self.num_state_qubits
            )
        }
        self._create_zero_input_registers({DEFAULT_INPUT_NAME: self.num_state_qubits})
