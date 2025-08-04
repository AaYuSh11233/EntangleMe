from typing import Callable, Union

import torch
from torch import Tensor

from classiq.interface.executor.execution_result import ResultsCollection, SavedResult

from classiq import QuantumProgram

Arguments = dict[str, float]
MultipleArguments = tuple[Arguments, ...]

Circuit = QuantumProgram
ExecuteFunction = Callable[[QuantumProgram, MultipleArguments], ResultsCollection]
ExecuteFuncitonOnlyArguments = Callable[[MultipleArguments], ResultsCollection]
PostProcessFunction = Callable[[SavedResult], Tensor]
TensorToArgumentsCallable = Callable[[Tensor, Tensor], MultipleArguments]

Shape = Union[torch.Size, tuple[int, ...]]

GradientFunction = Callable[[Tensor, Tensor], Tensor]
SimulateFunction = Callable[[Tensor, Tensor], Tensor]

DataAndLabel = tuple[list[int], Union[list[int], int]]
Transform = Callable[[Tensor], Tensor]
