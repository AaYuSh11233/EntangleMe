import json
from typing import Any, Optional, Protocol, TypeVar

import httpx
import pydantic
from pydantic.main import IncEx

import classiq.interface.executor.execution_result
import classiq.interface.pyomo_extension
from classiq.interface.analyzer import analysis_params, result as analysis_result
from classiq.interface.analyzer.analysis_params import AnalysisRBParams
from classiq.interface.analyzer.result import GraphStatus
from classiq.interface.chemistry import ground_state_problem, operator
from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqAPIError, ClassiqValueError
from classiq.interface.execution.iqcc import (
    IQCCAuthItemsDetails,
    IQCCInitAuthData,
    IQCCInitAuthResponse,
    IQCCListAuthMethods,
    IQCCListAuthTargets,
    IQCCProbeAuthData,
    IQCCProbeAuthResponse,
)
from classiq.interface.execution.primitives import PrimitivesInput
from classiq.interface.executor import execution_request, quantum_program_params
from classiq.interface.executor.quantum_program_params import (
    ParameterAssignmentsParams,
    TranspilationParams,
)
from classiq.interface.executor.user_budget import UserBudget
from classiq.interface.generator import quantum_program as generator_result
from classiq.interface.hardware import HardwareInformation, Provider
from classiq.interface.ide.visual_model import ProgramVisualModel
from classiq.interface.jobs import JobDescription, JobID, JSONObject
from classiq.interface.model.model import Model
from classiq.interface.server import routes

from classiq._internals.client import client
from classiq._internals.jobs import JobPoller

ResultType = TypeVar("ResultType", bound=pydantic.BaseModel)


class HTTPMethod(StrEnum):
    # Partial backport from Python 3.11
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"


class StatusType(Protocol):
    ERROR: str


def _parse_job_response(
    job_result: JobDescription[JSONObject],
    output_type: type[ResultType],
) -> ResultType:
    if job_result.result is not None:
        return output_type.model_validate(job_result.result)
    if job_result.failure_details:
        raise ClassiqAPIError(job_result.failure_details)

    raise ClassiqAPIError("Unexpected response from server")


class ApiWrapper:
    @classmethod
    async def _call_task_pydantic(
        cls,
        http_method: str,
        url: str,
        model: pydantic.BaseModel,
        use_versioned_url: bool = True,
        http_client: Optional[httpx.AsyncClient] = None,
        exclude: Optional[IncEx] = None,
    ) -> dict:
        # TODO: we can't use model.dict() - it doesn't serialize complex class.
        # This was added because JSON serializer doesn't serialize complex type, and pydantic does.
        # We should add support for smarter json serialization.
        body = json.loads(model.model_dump_json(exclude=exclude))
        return await cls._call_task(
            http_method,
            url,
            body,
            use_versioned_url=use_versioned_url,
            http_client=http_client,
        )

    @classmethod
    async def _call_task(
        cls,
        http_method: str,
        url: str,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        use_versioned_url: bool = True,
        headers: Optional[dict[str, str]] = None,
        allow_none: bool = False,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> dict:
        res: Any = await client().call_api(
            http_method=http_method,
            url=url,
            body=body,
            headers=headers,
            params=params,
            use_versioned_url=use_versioned_url,
            http_client=http_client,
        )
        if allow_none and res is None:
            return {}
        if not isinstance(res, dict):
            raise ClassiqValueError(f"Unexpected returned value: {res}")
        return res

    @classmethod
    async def _call_job_and_poll(
        cls,
        url: str,
        job_input: pydantic.BaseModel,
        result_type: type[ResultType],
        http_client: Optional[httpx.AsyncClient],
    ) -> ResultType:
        poller = JobPoller(base_url=url)
        result = await poller.run_pydantic(
            job_input, timeout_sec=None, http_client=http_client
        )
        return _parse_job_response(result, result_type)

    @classmethod
    async def call_generation_task(
        cls,
        model: Model,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        return await cls._call_job_and_poll(
            routes.TASKS_GENERATE_FULL_PATH,
            model,
            generator_result.QuantumProgram,
            http_client,
        )

    @classmethod
    async def call_transpilation_task(
        cls,
        params: TranspilationParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        return await cls._call_job_and_poll(
            routes.TRANSPILATION_FULL_PATH,
            params,
            generator_result.QuantumProgram,
            http_client,
        )

    @classmethod
    async def call_assign_parameters_task(
        cls,
        params: ParameterAssignmentsParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        return await cls._call_job_and_poll(
            routes.ASSIGN_PARAMETERS_FULL_PATH,
            params,
            generator_result.QuantumProgram,
            http_client,
        )

    @classmethod
    async def call_get_visual_model(
        cls,
        program_id: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProgramVisualModel:
        raw_result = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=f"{routes.ANALYZER_GET_VISUAL_MODEL_FULL_PATH}/{program_id}",
            http_client=http_client,
        )
        return ProgramVisualModel.model_validate(raw_result)

    @classmethod
    async def call_visualization_task(
        cls,
        circuit: generator_result.QuantumProgram,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProgramVisualModel:
        return await cls._call_job_and_poll(
            routes.TASKS_VISUAL_MODEL_FULL_PATH,
            circuit,
            ProgramVisualModel,
            http_client,
        )

    @classmethod
    async def call_create_execution_session(
        cls,
        circuit: generator_result.QuantumProgram,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> str:
        raw_result = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.EXECUTION_SESSIONS_PREFIX,
            model=circuit,
            http_client=http_client,
            exclude={"debug_info"},
        )
        return raw_result["id"]

    @classmethod
    async def call_create_session_job(
        cls,
        session_id: str,
        primitives_input: PrimitivesInput,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> execution_request.ExecutionJobDetails:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.EXECUTION_SESSIONS_PREFIX + f"/{session_id}",
            model=primitives_input,
            http_client=http_client,
        )
        return execution_request.ExecutionJobDetails.model_validate(data)

    @classmethod
    async def call_convert_quantum_program(
        cls,
        circuit: generator_result.QuantumProgram,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> dict:
        return await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.CONVERSION_GENERATED_CIRCUIT_TO_EXECUTION_INPUT_FULL,
            model=circuit,
            http_client=http_client,
            exclude={"debug_info"},
        )

    @classmethod
    async def transpile_quantum_program(
        cls,
        params: quantum_program_params.TranspilationParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.TRANSPILATION_FULL_PATH,
            model=params,
            http_client=http_client,
            exclude={"debug_info"},
        )
        return generator_result.QuantumProgram.model_validate(data)

    @classmethod
    async def assign_parameters_quantum_program(
        cls,
        params: quantum_program_params.ParameterAssignmentsParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.ASSIGN_PARAMETERS_FULL_PATH,
            model=params,
            http_client=http_client,
            exclude={"debug_info"},
        )
        return generator_result.QuantumProgram.model_validate(data)

    @classmethod
    async def call_execute_execution_input(
        cls,
        execution_input: dict,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> execution_request.ExecutionJobDetails:
        data = await cls._call_task(
            http_method=HTTPMethod.POST,
            url=routes.EXECUTION_JOBS_FULL_PATH,
            body=execution_input,
            http_client=http_client,
        )
        return execution_request.ExecutionJobDetails.model_validate(data)

    @classmethod
    async def call_get_execution_job_details(
        cls,
        job_id: JobID,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> execution_request.ExecutionJobDetails:
        data = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=f"{routes.EXECUTION_JOBS_FULL_PATH}/{job_id.job_id}",
            http_client=http_client,
        )
        return execution_request.ExecutionJobDetails.model_validate(data)

    @classmethod
    async def call_get_execution_job_result(
        cls,
        job_id: JobID,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> classiq.interface.executor.execution_result.ExecuteGeneratedCircuitResults:
        data = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=f"{routes.EXECUTION_JOBS_FULL_PATH}/{job_id.job_id}/result",
            http_client=http_client,
        )
        return classiq.interface.executor.execution_result.ExecuteGeneratedCircuitResults.model_validate(
            data
        )

    @classmethod
    async def call_patch_execution_job(
        cls,
        job_id: JobID,
        name: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> execution_request.ExecutionJobDetails:
        data = await cls._call_task(
            http_method=HTTPMethod.PATCH,
            url=f"{routes.EXECUTION_JOBS_FULL_PATH}/{job_id.job_id}",
            params={
                "name": name,
            },
            http_client=http_client,
        )
        return execution_request.ExecutionJobDetails.model_validate(data)

    @classmethod
    async def call_cancel_execution_job(
        cls,
        job_id: JobID,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        await cls._call_task(
            http_method=HTTPMethod.PUT,
            url=f"{routes.EXECUTION_JOBS_FULL_PATH}/{job_id.job_id}/cancel",
            allow_none=True,
            http_client=http_client,
        )

    @classmethod
    async def call_query_execution_jobs(
        cls,
        offset: int,
        limit: int,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> execution_request.ExecutionJobsQueryResults:
        data = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=f"{routes.EXECUTION_JOBS_FULL_PATH}",
            params={
                "offset": offset,
                "limit": limit,
            },
            http_client=http_client,
        )
        return execution_request.ExecutionJobsQueryResults.model_validate(data)

    @classmethod
    async def call_analysis_task(
        cls,
        params: analysis_params.AnalysisParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.Analysis:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.ANALYZER_FULL_PATH,
            model=params,
            http_client=http_client,
        )

        return analysis_result.Analysis.model_validate(data)

    @classmethod
    async def call_analyzer_app(
        cls,
        params: generator_result.QuantumProgram,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.DataID:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.ANALYZER_DATA_FULL_PATH,
            model=params,
            http_client=http_client,
        )
        return analysis_result.DataID.model_validate(data)

    @classmethod
    async def get_generated_circuit_from_qasm(
        cls,
        params: analysis_result.QasmCode,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.IDE_QASM_FULL_PATH,
            model=params,
            http_client=http_client,
        )
        return generator_result.QuantumProgram.model_validate(data)

    @classmethod
    async def get_analyzer_app_data(
        cls,
        params: analysis_result.DataID,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> generator_result.QuantumProgram:
        data = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=f"{routes.ANALYZER_DATA_FULL_PATH}/{params.id}",
            http_client=http_client,
        )
        return generator_result.QuantumProgram.model_validate(data)

    @classmethod
    async def call_rb_analysis_task(
        cls,
        params: AnalysisRBParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.RbResults:
        data = await cls._call_task(
            http_method=HTTPMethod.POST,
            url=routes.ANALYZER_RB_FULL_PATH,
            body=params.model_dump(),
            http_client=http_client,
        )

        return analysis_result.RbResults.model_validate(data)

    @classmethod
    async def call_hardware_connectivity_task(
        cls,
        params: analysis_params.AnalysisHardwareParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.GraphResult:
        data = await cls._call_task_pydantic(
            http_method=HTTPMethod.POST,
            url=routes.ANALYZER_HC_GRAPH_FULL_PATH,
            model=params,
            http_client=http_client,
        )
        return analysis_result.GraphResult.model_validate(data)

    @classmethod
    async def call_table_graphs_task(
        cls,
        params: analysis_params.AnalysisHardwareListParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.GraphResult:
        return await cls._call_job_and_poll(
            routes.ANALYZER_HC_TABLE_GRAPH_FULL_PATH,
            params,
            analysis_result.GraphResult,
            http_client,
        )

    @classmethod
    async def call_available_devices_task(
        cls,
        params: analysis_params.AnalysisOptionalDevicesParams,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> analysis_result.DevicesResult:
        hardware_info = await cls.call_get_all_hardware_devices(http_client=http_client)
        return cls._get_devices_from_hardware_info(hardware_info, params)

    @staticmethod
    def _get_devices_from_hardware_info(
        hardware_info: list[HardwareInformation],
        params: analysis_params.AnalysisOptionalDevicesParams,
    ) -> analysis_result.DevicesResult:
        available_hardware: dict[Provider, dict[str, bool]] = {
            Provider.IBM_QUANTUM: {},
            Provider.AMAZON_BRAKET: {},
            Provider.AZURE_QUANTUM: {},
        }
        for info in hardware_info:
            if info.provider not in available_hardware:
                continue
            is_available = info.number_of_qubits >= params.qubit_count
            available_hardware[info.provider][info.display_name] = is_available
        return analysis_result.DevicesResult(
            devices=analysis_result.AvailableHardware(
                ibm_quantum=available_hardware[Provider.IBM_QUANTUM],
                azure_quantum=available_hardware[Provider.AZURE_QUANTUM],
                amazon_braket=available_hardware[Provider.AMAZON_BRAKET],
            ),
            status=GraphStatus.SUCCESS,
        )

    @classmethod
    async def call_get_all_hardware_devices(
        cls,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> list[HardwareInformation]:
        data = await client().call_api(
            http_method=HTTPMethod.GET,
            url="/hardware-catalog/v1/hardwares",
            use_versioned_url=False,
            http_client=http_client,
        )
        if not isinstance(data, list):
            raise ClassiqAPIError(f"Unexpected value: {data}")
        return [HardwareInformation.model_validate(info) for info in data]

    @classmethod
    async def call_generate_hamiltonian_task(
        cls,
        problem: ground_state_problem.CHEMISTRY_PROBLEMS_TYPE,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> operator.PauliOperator:
        return await cls._call_job_and_poll(
            routes.GENERATE_HAMILTONIAN_FULL_PATH,
            problem,
            operator.PauliOperator,
            http_client,
        )

    @classmethod
    async def call_iqcc_init_auth(
        cls,
        data: IQCCInitAuthData,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> IQCCInitAuthResponse:
        response = await cls._call_task_pydantic(
            http_method=HTTPMethod.PUT,
            url=f"{routes.IQCC_INIT_AUTH_FULL_PATH}",
            model=data,
            http_client=http_client,
        )
        return IQCCInitAuthResponse.model_validate(response)

    @classmethod
    async def call_iqcc_probe_auth(
        cls,
        data: IQCCProbeAuthData,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[IQCCProbeAuthResponse]:
        try:
            response = await cls._call_task_pydantic(
                http_method=HTTPMethod.PUT,
                url=f"{routes.IQCC_PROBE_AUTH_FULL_PATH}",
                model=data,
                http_client=http_client,
            )
        except ClassiqAPIError as ex:
            if ex.status_code == 418:
                return None
            raise

        return IQCCProbeAuthResponse.model_validate(response)

    @classmethod
    async def call_iqcc_list_auth_scopes(
        cls,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> IQCCAuthItemsDetails:
        response = await cls._call_task(
            http_method=HTTPMethod.GET,
            url=routes.IQCC_LIST_AUTH_SCOPES_FULL_PATH,
            http_client=http_client,
        )
        return IQCCAuthItemsDetails.model_validate(response)

    @classmethod
    async def call_iqcc_list_auth_methods(
        cls,
        data: IQCCListAuthMethods,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> IQCCAuthItemsDetails:
        response = await cls._call_task_pydantic(
            http_method=HTTPMethod.PUT,
            url=routes.IQCC_LIST_AUTH_METHODS_FULL_PATH,
            model=data,
            http_client=http_client,
        )
        return IQCCAuthItemsDetails.model_validate(response)

    @classmethod
    async def call_iqcc_list_auth_targets(
        cls,
        data: IQCCListAuthTargets,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> IQCCAuthItemsDetails:
        response = await cls._call_task_pydantic(
            http_method=HTTPMethod.PUT,
            url=routes.IQCC_LIST_AUTH_TARGETS_FULL_PATH,
            model=data,
            http_client=http_client,
        )
        return IQCCAuthItemsDetails.model_validate(response)

    @classmethod
    async def call_get_all_budgets(cls) -> list[UserBudget]:
        data = await client().call_api(
            http_method=HTTPMethod.GET,
            url=routes.USER_BUDGETS_FULL_PATH,
        )

        return [UserBudget.model_validate(info) for info in data]

    @classmethod
    async def call_set_budget_limit(
        cls, provider: str, budget_limit: float
    ) -> UserBudget:
        data = await client().call_api(
            http_method=HTTPMethod.PATCH,
            url=routes.USER_BUDGET_SET_LIMIT_FULL_PATH,
            body={
                "provider": provider,
                "budget_limit": budget_limit,
            },
        )

        return UserBudget.model_validate(data)

    @classmethod
    async def call_clear_budget_limit(cls, provider: str) -> UserBudget:
        data = await client().call_api(
            http_method=HTTPMethod.PATCH,
            url=routes.USER_BUDGET_CLEAR_LIMIT_FULL_PATH,
            body={
                "provider": provider,
            },
        )

        return UserBudget.model_validate(data)
