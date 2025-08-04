import pydantic

from classiq.interface.chemistry import operator
from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
    FunctionParams,
    FunctionParamsNumericParameter,
)


class CommutingPauliExponentiation(FunctionParams):
    """
    Exponentiation of a Hermitian Pauli sum operator with commuting pauli strings.
    """

    pauli_operator: PauliOperator = pydantic.Field(
        description="A weighted sum of Pauli strings."
    )
    evolution_coefficient: FunctionParamsNumericParameter = pydantic.Field(
        default=1.0,
        description="A global coefficient multiplying the operator.",
    )

    @pydantic.field_validator("pauli_operator")
    @classmethod
    def _validate_is_hermitian(cls, pauli_operator: PauliOperator) -> PauliOperator:
        return operator.validate_operator_is_hermitian(pauli_operator)

    @pydantic.field_validator("pauli_operator")
    @classmethod
    def _validate_paulis_commute(cls, pauli_operator: PauliOperator) -> PauliOperator:
        if not pauli_operator.is_commutative:
            raise ClassiqValueError("Pauli strings are not commutative")
        return pauli_operator

    def _create_ios(self) -> None:
        size = self.pauli_operator.num_qubits
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterUserInput(name=DEFAULT_INPUT_NAME, size=size)
        }
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(name=DEFAULT_OUTPUT_NAME, size=size)
        }
