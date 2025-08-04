from pydantic import BaseModel, Field

from classiq.interface.executor.result import ExecutionDetails
from classiq.interface.generator.functions.classical_type import QmodPyObject
from classiq.interface.helpers.versioned_model import VersionedModel


class IQAEIterationData(BaseModel):
    """
    Handles the data storage for a single iteration of the Iterative Quantum Amplitude
    Estimation algorithm.

    This class is intended to represent the results and state of a single Grover iteration
    of the IQAE process.

    Attributes:
        grover_iterations (int): The iteration number of Grover's algorithm.
        sample_results (ExecutionDetails): The `ExecutionDetails` of Grover iteration. See ExecutionDetails.
    """

    grover_iterations: int
    sample_results: ExecutionDetails


class IQAEResult(VersionedModel, QmodPyObject):
    """
    Represents the result of an Iterative Quantum Amplitude Estimation (IQAE)
    process.

    This class encapsulates the output of the IQAE algorithm, including the
    estimated value, confidence interval, intermediate iteration data, and
    any warnings generated during the computation.

    Attributes:
        estimation (float): Estimation of the amplitude.
        confidence_interval (list[float]): The interval in which the amplitude is within, with a probability equal to epsilon.
        iterations_data (list[IQAEIterationData]): List of `IQAEIterationData` of each Grover iteration.
        See IQAEIterationData.
        warnings (list[str]): List of warnings generated during the IQAE process of each Grover iteration.
    """

    estimation: float
    confidence_interval: list[float] = Field(min_length=2, max_length=2)
    iterations_data: list[IQAEIterationData]
    warnings: list[str]
