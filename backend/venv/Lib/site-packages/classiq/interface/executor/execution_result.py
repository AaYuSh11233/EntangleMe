from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeAlias

from classiq.interface.applications.iqae.iqae_result import IQAEResult
from classiq.interface.enum_utils import StrEnum
from classiq.interface.executor.result import (
    EstimationResult,
    EstimationResults,
    ExecutionDetails,
    MultipleExecutionDetails,
)
from classiq.interface.executor.vqe_result import VQESolverResult
from classiq.interface.helpers.versioned_model import VersionedModel


class SavedResultValueType(StrEnum):
    Integer = "int"
    Float = "float"
    Boolean = "bool"
    VQESolverResult = "VQESolverResult"
    ExecutionDetails = "ExecutionDetails"
    MultipleExecutionDetails = "MultipleExecutionDetails"
    EstimationResult = "EstimationResult"
    EstimationResults = "EstimationResults"
    IQAEResult = "IQAEResult"
    MinimizeResult = "MinimizeResult"
    Unstructured = "Unstructured"


class TaggedInteger(BaseModel):
    value_type: Literal[SavedResultValueType.Integer]
    name: str
    value: int


class TaggedFloat(BaseModel):
    value_type: Literal[SavedResultValueType.Float]
    name: str
    value: float


class TaggedBoolean(BaseModel):
    value_type: Literal[SavedResultValueType.Boolean]
    name: str
    value: bool


class TaggedVQESolverResult(BaseModel):
    value_type: Literal[SavedResultValueType.VQESolverResult]
    name: str
    value: VQESolverResult


class TaggedExecutionDetails(BaseModel):
    value_type: Literal[SavedResultValueType.ExecutionDetails]
    name: str
    value: ExecutionDetails


class TaggedMultipleExecutionDetails(BaseModel):
    value_type: Literal[SavedResultValueType.MultipleExecutionDetails]
    name: str
    value: MultipleExecutionDetails


class TaggedEstimationResult(BaseModel):
    value_type: Literal[SavedResultValueType.EstimationResult]
    name: str
    value: EstimationResult


class TaggedEstimationResults(BaseModel):
    value_type: Literal[SavedResultValueType.EstimationResults]
    name: str
    value: EstimationResults


class TaggedIQAEResult(BaseModel):
    value_type: Literal[SavedResultValueType.IQAEResult]
    name: str
    value: IQAEResult


class TaggedUnstructured(BaseModel):
    value_type: Literal[SavedResultValueType.Unstructured]
    name: str
    value: Any = None


class SingleMinimizeResult(BaseModel):
    expectation_value: float
    parameters: list[float]


class TaggedMinimizeResult(BaseModel):
    value_type: Literal[SavedResultValueType.MinimizeResult]
    name: str
    value: list[SingleMinimizeResult]


SavedResult = Annotated[
    Union[
        TaggedInteger,
        TaggedFloat,
        TaggedBoolean,
        TaggedVQESolverResult,
        TaggedExecutionDetails,
        TaggedMultipleExecutionDetails,
        TaggedEstimationResult,
        TaggedEstimationResults,
        TaggedIQAEResult,
        TaggedUnstructured,
        TaggedMinimizeResult,
    ],
    Field(..., discriminator="value_type"),
]

ResultsCollection: TypeAlias = list[SavedResult]


class ExecuteGeneratedCircuitResults(VersionedModel):
    results: ResultsCollection

    model_config = ConfigDict(extra="forbid")
