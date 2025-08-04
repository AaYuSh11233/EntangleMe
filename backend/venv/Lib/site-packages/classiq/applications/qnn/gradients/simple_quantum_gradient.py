import itertools
from collections.abc import Iterable
from typing import Any

import torch
from torch import Tensor

from classiq import QuantumProgram
from classiq.applications.qnn.circuit_utils import (
    batch_map_parameters,
    is_single_layer_circuit,
)
from classiq.applications.qnn.gradients.quantum_gradient import QuantumGradient
from classiq.applications.qnn.torch_utils import iter_inputs_weights
from classiq.applications.qnn.types import (
    ExecuteFunction,
    MultipleArguments,
    PostProcessFunction,
    Shape,
    TensorToArgumentsCallable,
)

#
# Types
#
Sign = float  # only +1 or -1

#
# Gradient consts
#
EPSILON = 1e-2


def _add_epsilon(
    tensor: Tensor, index: int, sign: Sign = +1, epsilon: float = EPSILON
) -> Tensor:
    # Todo:
    #   - check how costly is `torch.zeros_like`
    #   - if it is, consider batching both calls (for sign=+1 and -1)
    epsilon_tensor = torch.zeros_like(tensor)
    epsilon_tensor[index] = epsilon

    return tensor + sign * epsilon_tensor


def _add_epsilon_to_tensor(
    tensor: Tensor, epsilon: float = EPSILON
) -> Iterable[Tensor]:
    return (
        _add_epsilon(tensor, index, sign, epsilon)
        for index in range(len(tensor))  # this is the first for-loop
        for sign in (+1, -1)  # this is the second
    )


def _differentiate_tensor(
    tensor: Tensor, axis: int = 3, epsilon: float = EPSILON
) -> Tensor:
    # The minus comes from the way pytorch defines diff
    #   it diffs the second object minus the first
    #     where we want the first minus the second
    diff = -tensor.diff(axis=axis).squeeze(axis)  # type: ignore[call-arg] # torch does accept `axis` keyword
    return diff / (2 * epsilon)


class SimpleQuantumGradient(QuantumGradient):
    def __init__(
        self,
        quantum_program: QuantumProgram,
        execute: ExecuteFunction,
        post_process: PostProcessFunction,
        epsilon: float = EPSILON,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(quantum_program, execute, post_process)
        self._epsilon = epsilon

    def _add_epsilon_to_tensor(self, tensor: Tensor) -> Iterable[Tensor]:
        return _add_epsilon_to_tensor(tensor, self._epsilon)

    def _convert_tensors_to_arguments(
        self, inputs_iterable: Iterable[Tensor], weights_iterable: Iterable[Tensor]
    ) -> MultipleArguments:
        return tuple(
            batch_map_parameters(
                self._parameters_names,
                inputs_iterable,
                weights_iterable,
            )
        )

    def convert_weights_tensors_to_arguments(
        self, inputs: Tensor, weights: Tensor
    ) -> MultipleArguments:
        return self._convert_tensors_to_arguments(
            itertools.repeat(inputs),
            self._add_epsilon_to_tensor(weights),
        )

    def convert_inputs_tensors_to_arguments(
        self, inputs: Tensor, weights: Tensor
    ) -> MultipleArguments:
        return self._convert_tensors_to_arguments(
            self._add_epsilon_to_tensor(inputs),
            itertools.repeat(weights),
        )

    def _differentiate_results(self, tensor: Tensor, axis: int) -> Tensor:
        # The `result` tensor is of the shape:
        #   (num_of_batches X num_of_weight_groups X num_of_weights_in_a_group X 2)
        #   where 2 is for 2 items : + and - epsilon
        #   and where num_of weight_groups can be omitted if it's 1.
        # We differentiate in num_of_weights_in_a_group which is specified by axis argument
        #   and is the one which is squeezed
        return _differentiate_tensor(tensor, axis=axis, epsilon=self._epsilon)

    def _gradient(
        self,
        inputs: Tensor,
        weights: Tensor,
        convert_tensors_to_arguments: TensorToArgumentsCallable,
        expected_shape: Shape,
    ) -> Tensor:
        result = iter_inputs_weights(
            inputs,
            weights,
            convert_tensors_to_arguments,
            self.execute,
            self._post_process,
            expected_shape=expected_shape,
        )

        axis_to_squeeze = 2 if is_single_layer_circuit(weights) else 3
        result = self._differentiate_results(result, axis_to_squeeze)

        result.requires_grad_(inputs.requires_grad or weights.requires_grad)
        return result

    def gradient_weights(
        self, inputs: Tensor, weights: Tensor, *args: Any, **kwargs: Any
    ) -> Tensor:
        return self._gradient(
            inputs,
            weights,
            self.convert_weights_tensors_to_arguments,
            expected_shape=(
                weights.shape[-1],
                2,
            ),
        )

    def gradient_inputs(
        self, inputs: Tensor, weights: Tensor, *args: Any, **kwargs: Any
    ) -> Tensor:
        return self._gradient(
            inputs,
            weights,
            self.convert_inputs_tensors_to_arguments,
            expected_shape=(
                inputs.shape[1],
                2,
            ),
        )
