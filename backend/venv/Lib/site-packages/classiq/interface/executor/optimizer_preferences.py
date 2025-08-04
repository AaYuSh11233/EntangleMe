from typing import Optional

import pydantic
from pydantic import BaseModel
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.helpers.custom_pydantic_types import PydanticAlphaParamCVAR


class CostType(StrEnum):
    MIN = "MIN"
    AVERAGE = "AVERAGE"
    CVAR = "CVAR"


class OptimizerType(StrEnum):
    COBYLA = "COBYLA"
    SPSA = "SPSA"
    L_BFGS_B = "L_BFGS_B"
    NELDER_MEAD = "NELDER_MEAD"
    ADAM = "ADAM"
    SLSQP = "SLSQP"


class OptimizerPreferences(BaseModel):
    name: OptimizerType = pydantic.Field(
        default=OptimizerType.COBYLA, description="Classical optimization algorithm."
    )
    num_shots: Optional[pydantic.PositiveInt] = pydantic.Field(
        default=None,
        description="Number of repetitions of the quantum ansatz.",
    )
    max_iteration: pydantic.PositiveInt = pydantic.Field(
        default=100, description="Maximal number of optimizer iterations"
    )
    tolerance: Optional[pydantic.PositiveFloat] = pydantic.Field(
        default=None, description="Final accuracy in the optimization"
    )
    step_size: Optional[pydantic.PositiveFloat] = pydantic.Field(
        default=None,
        description="step size for numerically " "calculating the gradient",
    )
    random_seed: Optional[int] = pydantic.Field(
        default=None,
        description="The random seed used for the generation",
    )
    initial_point: Optional[list[float]] = pydantic.Field(
        default=None,
        description="Initial values for the ansatz parameters",
    )
    skip_compute_variance: bool = pydantic.Field(
        default=False,
        description="If True, the optimizer will not compute the variance of the ansatz.",
    )

    @pydantic.field_validator("tolerance", mode="before")
    @classmethod
    def check_tolerance(
        cls, tolerance: Optional[pydantic.PositiveFloat], info: ValidationInfo
    ) -> Optional[pydantic.PositiveFloat]:
        optimizer_type = info.data.get("type")
        if tolerance is not None and optimizer_type == OptimizerType.SPSA:
            raise ClassiqValueError("No tolerance param for SPSA optimizer")

        if tolerance is None and optimizer_type != OptimizerType.SPSA:
            tolerance = pydantic.PositiveFloat(0.001)

        return tolerance

    @pydantic.field_validator("step_size", mode="before")
    @classmethod
    def check_step_size(
        cls, step_size: Optional[pydantic.PositiveFloat], info: ValidationInfo
    ) -> Optional[pydantic.PositiveFloat]:
        optimizer_type = info.data.get("name")
        if step_size is not None and optimizer_type not in (
            OptimizerType.L_BFGS_B,
            OptimizerType.ADAM,
        ):
            raise ClassiqValueError(
                "Use step_size only for L_BFGS_B or ADAM optimizers."
            )

        if step_size is None and optimizer_type in (
            OptimizerType.L_BFGS_B,
            OptimizerType.ADAM,
        ):
            step_size = pydantic.PositiveFloat(0.05)

        return step_size


class GroundStateOptimizer(OptimizerPreferences):
    pass


class CombinatorialOptimizer(OptimizerPreferences):
    cost_type: CostType = pydantic.Field(
        default=CostType.CVAR,
        description="Summarizing method of the measured bit strings",
    )
    alpha_cvar: Optional[PydanticAlphaParamCVAR] = pydantic.Field(
        default=None, description="Parameter for the CVAR summarizing method"
    )
    is_maximization: bool = pydantic.Field(
        default=False,
        description="Whether the optimization goal is to maximize",
    )
    should_check_valid_solutions: bool = pydantic.Field(
        default=False,
        description="Whether to check if all the solutions satisfy the constraints",
    )

    @pydantic.field_validator("alpha_cvar", mode="before")
    @classmethod
    def check_alpha_cvar(
        cls, alpha_cvar: Optional[PydanticAlphaParamCVAR], info: ValidationInfo
    ) -> Optional[PydanticAlphaParamCVAR]:
        cost_type = info.data.get("cost_type")
        if alpha_cvar is not None and cost_type != CostType.CVAR:
            raise ClassiqValueError("Use CVAR params only for CostType.CVAR.")

        if alpha_cvar is None and cost_type == CostType.CVAR:
            alpha_cvar = PydanticAlphaParamCVAR(0.2)

        return alpha_cvar
