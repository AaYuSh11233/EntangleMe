import pydantic
from pydantic import BaseModel

from classiq.interface.generator.finance import Finance


class FinanceModellingParams(BaseModel):
    finance_model: Finance = pydantic.Field(
        description="The model parameter for the finance problem."
    )
    phase_port_size: int = pydantic.Field(description="Width of the phase port.")
