import webbrowser
from datetime import datetime
from typing import Any, Optional, Union
from urllib.parse import urljoin

import httpx

from classiq.interface.exceptions import (
    ClassiqAPIError,
    ClassiqError,
)
from classiq.interface.executor.execution_request import ExecutionJobDetails, JobCost
from classiq.interface.executor.execution_result import (
    ResultsCollection,
    TaggedMinimizeResult,
)
from classiq.interface.executor.result import (
    EstimationResult,
    EstimationResults,
    ExecutionDetails,
    MultipleExecutionDetails,
)
from classiq.interface.jobs import JobStatus, JSONObject
from classiq.interface.server.routes import EXECUTION_JOBS_FULL_PATH

from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.async_utils import syncify_function
from classiq._internals.client import client
from classiq._internals.jobs import JobID, JobPoller


class ClassiqExecutionResultError(ClassiqError):
    def __init__(self, primitive: str) -> None:
        super().__init__(
            f"Execution job does not contain a single {primitive!r} result, make sure you use the 'get_*_result' method matching the primitive you executed. You can use the 'result' method to see the general result."
        )


class ExecutionJob:
    _details: ExecutionJobDetails
    _result: Optional[ResultsCollection]

    def __init__(self, details: ExecutionJobDetails) -> None:
        self._details = details
        self._result = None

    @property
    def id(self) -> str:
        return self._details.id

    @property
    def name(self) -> Optional[str]:
        return self._details.name

    @property
    def start_time(self) -> datetime:
        return self._details.start_time

    @property
    def end_time(self) -> Optional[datetime]:
        return self._details.end_time

    @property
    def provider(self) -> Optional[str]:
        return self._details.provider

    @property
    def backend_name(self) -> Optional[str]:
        return self._details.backend_name

    @property
    def status(self) -> JobStatus:
        return self._details.status

    @property
    def num_shots(self) -> Optional[int]:
        return self._details.num_shots

    @property
    def program_id(self) -> Optional[str]:
        return self._details.program_id

    @property
    def error(self) -> Optional[str]:
        return self._details.error

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        if self.name is None:
            return f"{class_name}(id={self.id!r})"
        else:
            return f"{class_name}(name={self.name!r}, id={self.id!r})"

    def cost(self, *, verbose: bool = False) -> Union[str, JobCost]:
        if self._details.cost is None:
            self._details.cost = JobCost()
        if verbose:
            return self._details.cost
        return f"{self._details.cost.total_cost} {self._details.cost.currency_code}"

    @classmethod
    async def from_id_async(
        cls,
        id: str,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> "ExecutionJob":
        details = await ApiWrapper.call_get_execution_job_details(
            JobID(job_id=id), http_client=_http_client
        )
        return cls(details)

    # `syncify_function` doesn't work well for class methods, so I wrote `from_id`
    # explicitly
    @classmethod
    def from_id(
        cls,
        id: str,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> "ExecutionJob":
        return syncify_function(cls.from_id_async)(id, _http_client=_http_client)

    @property
    def _job_id(self) -> JobID:
        return JobID(job_id=self.id)

    async def result_async(
        self,
        timeout_sec: Optional[float] = None,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> ResultsCollection:
        await self.poll_async(timeout_sec=timeout_sec, _http_client=_http_client)

        if self.status == JobStatus.FAILED:
            raise ClassiqAPIError(self.error or "")
        if self.status == JobStatus.CANCELLED:
            raise ClassiqAPIError("Job has been cancelled.")

        if self._result is None:
            self._result = (
                await ApiWrapper.call_get_execution_job_result(
                    job_id=self._job_id,
                    http_client=_http_client,
                )
            ).results
        return self._result

    result = syncify_function(result_async)

    def result_value(self, *args: Any, **kwargs: Any) -> Any:
        return self.result(*args, **kwargs)[0].value

    def get_sample_result(
        self, _http_client: Optional[httpx.AsyncClient] = None
    ) -> ExecutionDetails:
        """
        Returns the job's result as a single sample result after validation. If the result is not yet available, waits for it.

        Returns:
            The sample result of the execution job.

        Raises:
            ClassiqExecutionResultError: In case the result does not contain a single sample result.
            ClassiqAPIError: In case the job has failed.
        """
        results = self.result(_http_client=_http_client)
        if len(results) != 1:
            raise ClassiqExecutionResultError("sample")

        result = results[0].value
        if isinstance(result, ExecutionDetails):
            return result
        if isinstance(result, MultipleExecutionDetails) and len(result.details) == 1:
            return result.details[0]
        raise ClassiqExecutionResultError("sample")

    def get_batch_sample_result(
        self, _http_client: Optional[httpx.AsyncClient] = None
    ) -> list[ExecutionDetails]:
        """
        Returns the job's result as a single batch_sample result after validation. If the result is not yet available, waits for it.

        Returns:
            The batch_sample result of the execution job.

        Raises:
            ClassiqExecutionResultError: In case the result does not contain a single batch_sample result.
            ClassiqAPIError: In case the job has failed.
        """
        results = self.result(_http_client=_http_client)
        if len(results) != 1:
            raise ClassiqExecutionResultError("batch_sample")

        result = results[0].value
        if isinstance(result, ExecutionDetails):
            return [result]
        if isinstance(result, MultipleExecutionDetails):
            return result.details

        raise ClassiqExecutionResultError("batch_sample")

    def get_estimate_result(
        self, _http_client: Optional[httpx.AsyncClient] = None
    ) -> EstimationResult:
        """
        Returns the job's result as a single estimate result after validation. If the result is not yet available, waits for it.

        Returns:
            The estimate result of the execution job.

        Raises:
            ClassiqExecutionResultError: In case the result does not contain a single estimate result.
            ClassiqAPIError: In case the job has failed.
        """
        results = self.result(_http_client=_http_client)
        if len(results) != 1:
            raise ClassiqExecutionResultError("estimate")

        result = results[0].value
        if isinstance(result, EstimationResult):
            return result
        if isinstance(result, EstimationResults) and len(result.results) == 1:
            return result.results[0]
        raise ClassiqExecutionResultError("estimate")

    def get_batch_estimate_result(
        self, _http_client: Optional[httpx.AsyncClient] = None
    ) -> list[EstimationResult]:
        """
        Returns the job's result as a single batch_estimate result after validation. If the result is not yet available, waits for it.

        Returns:
            The batch_estimate result of the execution job.

        Raises:
            ClassiqExecutionResultError: In case the result does not contain a single batch_estimate result.
            ClassiqAPIError: In case the job has failed.
        """
        results = self.result(_http_client=_http_client)
        if len(results) != 1:
            raise ClassiqExecutionResultError("batch_estimate")

        result = results[0].value
        if isinstance(result, EstimationResult):
            return [result]
        if isinstance(result, EstimationResults):
            return result.results

        raise ClassiqExecutionResultError("batch_estimate")

    def get_minimization_result(
        self, _http_client: Optional[httpx.AsyncClient] = None
    ) -> TaggedMinimizeResult:
        """
        Returns the job's result as a single minimization result after validation. If the result is not yet available, waits for it.

        Returns:
            The minimization result of the execution job.

        Raises:
            ClassiqExecutionResultError: In case the result does not contain a single minimization result.
            ClassiqAPIError: In case the job has failed.
        """
        results = self.result(_http_client=_http_client)
        if len(results) != 1:
            raise ClassiqExecutionResultError("minimization")

        result = results[0]
        if isinstance(result, TaggedMinimizeResult):
            return result
        raise ClassiqExecutionResultError("minimization")

    async def poll_async(
        self,
        timeout_sec: Optional[float] = None,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if not self.status.is_final():
            await self._poll_job(timeout_sec=timeout_sec, _http_client=_http_client)

    poll = syncify_function(poll_async)

    async def _poll_job(
        self,
        timeout_sec: Optional[float] = None,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        def response_parser(json_response: JSONObject) -> Optional[bool]:
            self._details = ExecutionJobDetails.model_validate(json_response)
            if self.status.is_final():
                return True
            return None

        poller = JobPoller(
            base_url=EXECUTION_JOBS_FULL_PATH,
        )
        await poller.poll(
            job_id=self._job_id,
            response_parser=response_parser,
            timeout_sec=timeout_sec,
            http_client=_http_client,
        )

    async def rename_async(
        self,
        name: str,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._details = await ApiWrapper.call_patch_execution_job(
            self._job_id,
            name,
            http_client=_http_client,
        )

    rename = syncify_function(rename_async)

    async def cancel_async(
        self,
        _http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """
        Cancels the execution job. This implies the cancellation of any ongoing jobs
        sent to the provider during this execution job.

        The function returns without waiting to the actual cancellation. It is possible
        to continue polling the job in order to ensure its cancellation, which might
        not be immediate.
        """
        await ApiWrapper.call_cancel_execution_job(
            self._job_id,
            http_client=_http_client,
        )

    cancel = syncify_function(cancel_async)

    @property
    def ide_url(self) -> str:
        base_url = client().config.ide.unicode_string()
        return urljoin(base_url, f"jobs/{self.id}")

    def open_in_ide(self) -> None:
        webbrowser.open_new_tab(self.ide_url)


async def get_execution_jobs_async(
    offset: int = 0, limit: int = 50
) -> list[ExecutionJob]:
    result = await ApiWrapper().call_query_execution_jobs(offset=offset, limit=limit)
    return [ExecutionJob(details) for details in result.results]


get_execution_jobs = syncify_function(get_execution_jobs_async)
