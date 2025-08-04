from typing import Any, Generic, Optional, TypeVar, Union

import pydantic
from pydantic import BaseModel
from typing_extensions import Self

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqAPIError
from classiq.interface.helpers.custom_encoders import CUSTOM_ENCODERS

JSONObject = dict[str, Any]
T = TypeVar("T", bound=Union[pydantic.BaseModel, JSONObject])
AUTH_HEADER = "Classiq-BE-Auth"
INVALID_RESPONSE_ERROR_MSG = "Invalid response from Classiq API"


class JobID(BaseModel):
    job_id: str


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"

    def is_final(self) -> bool:
        return self in (self.COMPLETED, self.FAILED, self.CANCELLED)


"""
A job can be in either of 3 states: ongoing, completed successfully or completed
unsuccessfully. Each job status belongs to one of the 3 states
For ongoing jobs, we expect both the failure_details and result to be None
For successful jobs, we expect failure_details to be None and result to be an instance of T
For unsuccessful jobs, we expect failure_details to be a string and result to be None
"""


class JobDescription(BaseModel, Generic[T], json_encoders=CUSTOM_ENCODERS):
    status: JobStatus
    failure_details: Optional[str] = pydantic.Field(default=None)
    result: Optional[T] = pydantic.Field(default=None)

    @pydantic.model_validator(mode="after")
    def validate_status_and_fields(self) -> Self:
        if self.status is JobStatus.COMPLETED:
            # Completed job must return result and not have an error
            if self.result is None or self.failure_details is not None:
                raise ClassiqAPIError(INVALID_RESPONSE_ERROR_MSG)
        elif self.status in (JobStatus.FAILED, JobStatus.CANCELLED):
            # Failed job must return error and not have result
            if self.result is not None or self.failure_details is None:
                raise ClassiqAPIError(INVALID_RESPONSE_ERROR_MSG)
        elif self.result is not None or self.failure_details is not None:
            # Pending job must have no result and no error
            raise ClassiqAPIError(INVALID_RESPONSE_ERROR_MSG)

        return self
