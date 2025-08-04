from __future__ import annotations

from typing import Union

import pydantic

from classiq.interface.finance.function_input import FinanceFunctionInput
from classiq.interface.finance.gaussian_model_input import GaussianModelInput
from classiq.interface.finance.log_normal_model_input import LogNormalModelInput
from classiq.interface.generator import function_params
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import DEFAULT_ZERO_NAME

FUNCTION_INPUT_NAME = "function_in"
FUNCTION_OUTPUT_NAME = "function_out"
OBJECTIVE_INPUT_NAME = "objective_in"
OBJECTIVE_OUTPUT_NAME = "objective_out"
DEFAULT_POST_INPUT_NAME = "post_function_input"


class Finance(function_params.FunctionParams):
    model: Union[GaussianModelInput, LogNormalModelInput] = pydantic.Field(
        description="Load a financial model", discriminator="kind"
    )
    finance_function: FinanceFunctionInput = pydantic.Field(
        description="The finance function to solve the model"
    )

    def _create_ios(self) -> None:
        finance_model = FinanceModels(model=self.model)
        # 1 for the objective qubit
        function_size = sum(
            reg.size for reg in finance_model._outputs.values() if reg is not None
        )
        self._inputs = {
            FUNCTION_INPUT_NAME: RegisterUserInput(
                name=FUNCTION_INPUT_NAME, size=function_size
            ),
            OBJECTIVE_INPUT_NAME: RegisterUserInput(name=OBJECTIVE_INPUT_NAME, size=1),
        }
        self._outputs = {
            FUNCTION_OUTPUT_NAME: RegisterUserInput(
                name=FUNCTION_OUTPUT_NAME, size=function_size
            ),
            OBJECTIVE_OUTPUT_NAME: RegisterUserInput(
                name=OBJECTIVE_OUTPUT_NAME, size=1
            ),
        }


DEFAULT_INPUT_NAME = "in"
DEFAULT_OUTPUT_NAME = "out"
DEFAULT_BERNOULLI_OUTPUT_NAME = "bernoulli_random_variables"


class FinanceModels(function_params.FunctionParams):
    model: Union[GaussianModelInput, LogNormalModelInput] = pydantic.Field(
        description="Load a financial model"
    )

    def _create_ios(self) -> None:
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(
                name=DEFAULT_OUTPUT_NAME, size=self.model.num_output_qubits
            )
        }
        if isinstance(self.model, GaussianModelInput):
            self._inputs = {
                DEFAULT_INPUT_NAME: RegisterUserInput(
                    name=DEFAULT_INPUT_NAME, size=self.model.num_bernoulli_qubits
                )
            }
            self._create_zero_input_registers(
                {DEFAULT_ZERO_NAME: self.model.num_output_qubits}
            )
            self._outputs[DEFAULT_BERNOULLI_OUTPUT_NAME] = RegisterUserInput(
                name=DEFAULT_BERNOULLI_OUTPUT_NAME,
                size=self.model.num_bernoulli_qubits,
            )
        elif isinstance(self.model, LogNormalModelInput):
            self._inputs = {
                DEFAULT_INPUT_NAME: RegisterUserInput(
                    name=DEFAULT_INPUT_NAME, size=self.model.num_model_qubits
                )
            }


class FinancePayoff(function_params.FunctionParams):
    finance_function: FinanceFunctionInput = pydantic.Field(
        description="The finance function to solve the model"
    )
    num_qubits: pydantic.PositiveInt
    distribution_range: tuple[float, float]

    def _create_ios(self) -> None:
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterUserInput(
                name=DEFAULT_INPUT_NAME, size=self.num_qubits
            )
        }
        self._create_zero_input_registers({DEFAULT_ZERO_NAME: 1})
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(name=DEFAULT_OUTPUT_NAME, size=1),
            DEFAULT_POST_INPUT_NAME: RegisterUserInput(
                name=DEFAULT_INPUT_NAME, size=self.num_qubits
            ),
        }
