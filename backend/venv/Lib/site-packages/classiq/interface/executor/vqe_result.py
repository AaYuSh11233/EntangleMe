import base64
import io
from datetime import datetime
from typing import Optional

import pydantic
from PIL import Image
from pydantic import BaseModel

from classiq.interface.executor.result import ExecutionDetails
from classiq.interface.generator.complex_type import Complex
from classiq.interface.generator.functions.classical_type import QmodPyObject
from classiq.interface.helpers.custom_pydantic_types import PydanticProbabilityFloat

Solution = tuple[int, ...]


class SolverResult(BaseModel):
    energy: float
    # TODO: add time units (like seconds)
    time: Optional[float] = None
    solution: Optional[Solution] = None


class SolutionData(BaseModel):
    solution: Solution
    repetitions: pydantic.PositiveInt
    probability: PydanticProbabilityFloat
    cost: float


class VQEIntermediateData(BaseModel):
    utc_time: datetime = pydantic.Field(description="Time when the iteration finished")
    iteration_number: pydantic.PositiveInt = pydantic.Field(
        description="The iteration's number (evaluation count)"
    )
    parameters: list[float] = pydantic.Field(
        description="The optimizer parameters for the variational form"
    )
    mean_all_solutions: Optional[float] = pydantic.Field(
        default=None, description="The mean score of all solutions in this iteration"
    )
    solutions: list[SolutionData] = pydantic.Field(
        description="Solutions found in this iteration, their score and"
        "number of repetitions"
    )
    standard_deviation: float = pydantic.Field(
        description="The evaluated standard deviation"
    )


class VQESolverResult(SolverResult, QmodPyObject):
    eigenstate: dict[str, Complex]
    reduced_probabilities: Optional[dict[str, float]] = None
    optimized_circuit_sample_results: ExecutionDetails
    intermediate_results: list[VQEIntermediateData]
    optimal_parameters: dict[str, float]
    convergence_graph_str: str
    num_solutions: Optional[int] = None
    num_shots: int

    def show_convergence_graph(self) -> None:
        self.convergence_graph.show()

    @property
    def convergence_graph(self) -> Image.Image:
        return Image.open(io.BytesIO(base64.b64decode(self.convergence_graph_str)))

    @property
    def energy_std(self) -> float:
        return self.intermediate_results[-1].standard_deviation
