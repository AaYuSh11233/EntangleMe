from typing import Union

import numpy as np
import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator import complex_type, function_params
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo

DataNumber = Union[complex_type.Complex, float, int]
DataArray = list[list[DataNumber]]

UNITARY_GATE_INPUT: str = "TARGET"
UNITARY_GATE_OUTPUT: str = "TARGET"


class UnitaryGate(function_params.FunctionParams):
    """
    Creates a circuit implementing a specified 2**n * 2**n unitary transformation.
    """

    # TODO - add support to numpy array-like (requires custom pydantic type definition)
    data: DataArray = pydantic.Field(
        description="A 2**n * 2**n (n positive integer) unitary matrix."
    )

    # TODO - decide if to include assertion on the unitarity of the matrix. It is already done in Qiskit and could be computationally expensive
    @pydantic.field_validator("data")
    @classmethod
    def validate_data(cls, data: DataArray) -> DataArray:
        data_np = np.array(data, dtype=object)
        if data_np.ndim != 2:
            raise ClassiqValueError("Data must me two dimensional")
        if data_np.shape[0] != data_np.shape[1]:
            raise ClassiqValueError("Matrix must be square")
        if not np.mod(np.log2(data_np.shape[0]), 1) == 0:
            raise ClassiqValueError(
                "Matrix dimensions must be an integer exponent of 2"
            )
        return data

    @property
    def num_target_qubits(self) -> int:
        return int(np.log2(len(self.data)))

    def _create_ios(self) -> None:
        self._inputs = {
            UNITARY_GATE_INPUT: RegisterArithmeticInfo(size=self.num_target_qubits)
        }
        self._outputs = {
            UNITARY_GATE_OUTPUT: RegisterArithmeticInfo(size=self.num_target_qubits)
        }
