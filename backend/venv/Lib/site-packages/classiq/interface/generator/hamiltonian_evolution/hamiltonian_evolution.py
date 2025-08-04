from abc import ABC

import pydantic

from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
    FunctionParams,
)


class HamiltonianEvolution(FunctionParams, ABC):
    """
    Suzuki trotterization of a Hermitian operator
    """

    pauli_operator: PauliOperator = pydantic.Field(
        description="A weighted sum of Pauli strings."
    )
    use_naive_evolution: bool = pydantic.Field(
        default=False, description="Whether to evolve the operator naively."
    )

    def _create_ios(self) -> None:
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterArithmeticInfo(
                size=self.pauli_operator.num_qubits
            )
        }
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterArithmeticInfo(
                size=self.pauli_operator.num_qubits
            )
        }
