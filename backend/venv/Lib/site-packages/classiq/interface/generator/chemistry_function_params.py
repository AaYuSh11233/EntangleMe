import pydantic

from classiq.interface.chemistry.ground_state_problem import (
    CHEMISTRY_PROBLEMS_TYPE,
    GroundStateProblem,
)
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
    FunctionParams,
)


class ChemistryFunctionParams(FunctionParams):
    gs_problem: CHEMISTRY_PROBLEMS_TYPE

    @pydantic.field_validator("gs_problem")
    @classmethod
    def validate_gs_problem_contains_num_qubits(
        cls, gs_problem: CHEMISTRY_PROBLEMS_TYPE
    ) -> CHEMISTRY_PROBLEMS_TYPE:
        if not gs_problem.num_qubits:
            raise ClassiqValueError(
                "Ground state problem doesn't contain num_qubits. "
                "Use update_problem method."
            )

        return gs_problem

    @property
    def num_qubits(self) -> int:
        assert isinstance(
            self.gs_problem, GroundStateProblem
        ), "self.gs_problem is not from GroundStateProblem class"
        assert isinstance(self.gs_problem.num_qubits, int)
        return self.gs_problem.num_qubits

    def _create_ios(self) -> None:
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterUserInput(
                name=DEFAULT_INPUT_NAME, size=self.num_qubits
            )
        }
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(
                name=DEFAULT_OUTPUT_NAME, size=self.num_qubits
            )
        }
