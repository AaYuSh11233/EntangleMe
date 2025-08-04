from typing import Any

import pydantic
from pydantic import BaseModel

from classiq.interface.executor.optimizer_preferences import CombinatorialOptimizer


class MaxCutProblem(BaseModel):
    qaoa_reps: pydantic.PositiveInt = pydantic.Field(
        default=1, description="Number of layers in qaoa ansatz."
    )
    optimizer_preferences: CombinatorialOptimizer = pydantic.Field(
        default_factory=CombinatorialOptimizer,
        description="preferences for the VQE execution",
    )
    serialized_graph: dict[str, Any]
