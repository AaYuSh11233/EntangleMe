from typing import Literal

import numpy as np
import pydantic
from pydantic import ConfigDict

from classiq.interface.finance.model_input import FinanceModelInput


class LogNormalModelInput(FinanceModelInput):
    kind: Literal["log_normal"] = pydantic.Field(default="log_normal")

    num_qubits: pydantic.PositiveInt = pydantic.Field(
        description="Number of qubits to represent the probability."
    )
    mu: pydantic.NonNegativeFloat = pydantic.Field(
        description="Mean of the Normal distribution variable X s.t. ln(X) ~ log-normal."
    )
    sigma: pydantic.PositiveFloat = pydantic.Field(
        description="Std of the Normal distribution variable X s.t. ln(X) ~ log-normal."
    )

    @property
    def distribution_range(self) -> tuple[float, float]:
        mean = np.exp(self.mu + self.sigma**2 / 2)
        variance = (np.exp(self.sigma**2) - 1) * np.exp(2 * self.mu + self.sigma**2)
        stddev = np.sqrt(variance)
        low = np.maximum(0, mean - 3 * stddev)
        high = mean + 3 * stddev
        return low, high

    @property
    def num_model_qubits(self) -> int:
        return self.num_qubits

    @property
    def num_output_qubits(self) -> int:
        return self.num_qubits

    model_config = ConfigDict(frozen=True)
