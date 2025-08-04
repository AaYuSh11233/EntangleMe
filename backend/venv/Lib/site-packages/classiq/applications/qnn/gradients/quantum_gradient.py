import abc
import functools
from typing import Any

from torch import Tensor

from classiq.interface.generator.quantum_program import QuantumProgram

from classiq.applications.qnn.circuit_utils import extract_parameters, validate_circuit
from classiq.applications.qnn.types import ExecuteFunction, PostProcessFunction


class QuantumGradient(abc.ABC):
    def __init__(
        self,
        quantum_program: QuantumProgram,
        execute: ExecuteFunction,
        post_process: PostProcessFunction,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._execute = execute
        self._post_process = post_process

        validate_circuit(quantum_program)
        self._quantum_program = quantum_program
        self._parameters_names = extract_parameters(quantum_program)

        self.execute = functools.partial(execute, quantum_program)

    @abc.abstractmethod
    def gradient_weights(
        self, inputs: Tensor, weights: Tensor, *args: Any, **kwargs: Any
    ) -> Tensor:
        pass

    @abc.abstractmethod
    def gradient_inputs(
        self, inputs: Tensor, weights: Tensor, *args: Any, **kwargs: Any
    ) -> Tensor:
        pass
