from itertools import chain
from typing import Optional

import pydantic
import sympy
from typing_extensions import Self

from classiq.interface.backend.pydantic_backend import PydanticExecutionParameter
from classiq.interface.generator.parameters import ParameterType


class FunctionExecutionData(pydantic.BaseModel):
    power_parameter: Optional[ParameterType] = pydantic.Field(default=None)

    @property
    def power_vars(self) -> Optional[list[str]]:
        if self.power_parameter is None:
            return None
        return list(map(str, sympy.sympify(self.power_parameter).free_symbols))


class ExecutionData(pydantic.BaseModel):
    function_execution: dict[str, FunctionExecutionData] = pydantic.Field(
        default_factory=dict
    )

    @property
    def execution_parameters(
        self,
    ) -> set[PydanticExecutionParameter]:
        return set(
            chain.from_iterable(
                function_execution_data.power_vars
                for function_execution_data in self.function_execution.values()
                if function_execution_data.power_vars is not None
            )
        )

    def to_inverse(self) -> Self:
        return type(self)(
            function_execution={
                self._inverse_name(name): value
                for name, value in self.function_execution.items()
            }
        )

    def to_control(self) -> Self:
        return type(self)(
            function_execution={
                self._control_name(name): value
                for name, value in self.function_execution.items()
            }
        )

    @staticmethod
    def _inverse_name(name: str) -> str:
        # see inverse of qiskit.circuit.Instruction
        if name.endswith("_dg"):
            return name[:-3]
        return f"{name}_dg"

    @staticmethod
    def _control_name(name: str) -> str:
        # see inverse of qiskit.circuit.QuantumCircuit
        return f"c_{name}"
