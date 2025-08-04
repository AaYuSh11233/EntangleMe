from collections.abc import Sized
from functools import reduce
from typing import Optional

import torch
import torch.nn as nn
from torch import Tensor

from classiq.interface.exceptions import ClassiqValueError

from classiq.applications.qnn.circuit_utils import is_single_layer_circuit
from classiq.applications.qnn.types import (
    ExecuteFuncitonOnlyArguments,
    PostProcessFunction,
    Shape,
    TensorToArgumentsCallable,
)


def get_shape_second_dimension(shape: torch.Size) -> int:
    if not isinstance(shape, Sized):
        raise ClassiqValueError("Invalid shape type - must have `__len__`")

    if len(shape) == 1:
        return 1
    elif len(shape) == 2:
        return shape[1]
    else:
        raise ClassiqValueError("Invalid shape dimension - must be 1D or 2D")


def get_shape_first_dimension(shape: torch.Size) -> int:
    if not isinstance(shape, Sized):
        raise ClassiqValueError("Invalid shape type - must have `__len__`")

    if len(shape) in (1, 2):
        return shape[0]
    else:
        raise ClassiqValueError("Invalid shape dimension - must be 1D or 2D")


def _set_tensor_attributes(
    t: Tensor,
    dtype: torch.dtype,
    requires_grad: bool,
    expected_shape: Shape,
) -> Tensor:
    return t.to(dtype).requires_grad_(requires_grad).reshape(*expected_shape)


def _result_to_tensor(
    all_results: list,
    inputs: Tensor,
    weights: Tensor,
    expected_shape: Optional[Shape] = None,
    requires_grad: Optional[bool] = None,
) -> Tensor:
    default_shape = (
        torch.Size([inputs.shape[0]])
        if is_single_layer_circuit(weights)
        else (
            torch.Size(
                [
                    inputs.shape[0],  # batch size
                    weights.shape[0],  # num circuits
                ]
            )
        )
    )
    expected_shape = expected_shape or default_shape

    # Note: we chose `dtype=weights.dtype`
    #   we could have chosen `dtype=inputs.dtype`
    #   It would be nearly identical
    #   but choosing weights is better since it must be some float
    #       in order to have a tensor derivative
    dtype = weights.dtype

    # Todo: when creating this tensor, we set `requires_grad`, but don't define `grad_fn`
    #   This may cause problems later. Thus, we'll deal with it later.
    if requires_grad is None:
        requires_grad = inputs.requires_grad or weights.requires_grad

    return _set_tensor_attributes(
        torch.stack(all_results), dtype, requires_grad, expected_shape
    )


def iter_inputs_weights(
    inputs: Tensor,
    weights: Tensor,
    convert_tensors_to_arguments: TensorToArgumentsCallable,
    execute: ExecuteFuncitonOnlyArguments,
    post_process: PostProcessFunction,
    *,
    expected_shape: Shape = (),
    requires_grad: Optional[bool] = None,
) -> Tensor:
    if is_single_layer_circuit(weights):
        iter_weights = torch.reshape(weights, (1, weights.shape[0]))
        inputs_weights_shape: tuple[int, ...] = (inputs.shape[0],)
    else:
        iter_weights = weights
        inputs_weights_shape = (inputs.shape[0], weights.shape[0])
    all_arguments = sum(
        (
            convert_tensors_to_arguments(batch_item, out_weight)
            for batch_item in inputs  # this is the first for-loop
            for out_weight in iter_weights  # this is the second
        ),
        (),
    )

    execution_results = execute(all_arguments)

    all_results = list(map(post_process, execution_results))

    expected_shape = inputs_weights_shape + expected_shape + all_results[0].shape

    return _result_to_tensor(
        all_results, inputs, weights, expected_shape, requires_grad
    )


def einsum_weigths(
    grad_output: Tensor, grad_weights: Tensor, is_single_layer: bool = False
) -> Tensor:
    if is_single_layer:
        return torch.einsum("i...,il...->l", grad_output, grad_weights)
    return torch.einsum("ip...,ipl...->pl", grad_output, grad_weights)


def einsum_inputs(
    grad_output: Tensor, grad_inputs: Tensor, is_single_layer: bool = False
) -> Tensor:
    if is_single_layer:
        return torch.einsum("i...,ij...->ij", grad_output, grad_inputs)
    return torch.einsum("ip...,ipj...->ij", grad_output, grad_inputs)


def calculate_amount_of_parameters(net: nn.Module) -> int:
    return sum(  # sum over all parameters
        reduce(int.__mul__, i.shape)  # multiply all dimensions
        for i in net.parameters()
    )
