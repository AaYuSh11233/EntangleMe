import inspect
import random
import warnings
from types import TracebackType
from typing import Any, Callable, Optional, Union, cast

from classiq.interface.chemistry.operator import PauliOperator, pauli_integers_to_str
from classiq.interface.exceptions import (
    ClassiqDeprecationWarning,
    ClassiqError,
    ClassiqValueError,
)
from classiq.interface.execution.primitives import (
    EstimateInput,
    MinimizeClassicalCostInput,
    MinimizeQuantumCostInput,
    PrimitivesInput,
)
from classiq.interface.executor.estimate_cost import estimate_cost
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.executor.execution_result import TaggedMinimizeResult
from classiq.interface.executor.result import (
    EstimationResult,
    ExecutionDetails,
    ParsedState,
)
from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.qmod_python_interface import QmodPyStruct
from classiq.interface.generator.quantum_program import (
    QuantumProgram,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticPauliList
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumNumeric,
    RegisterQuantumTypeDict,
)

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.client import client
from classiq.applications.combinatorial_helpers.pauli_helpers.pauli_utils import (
    _pauli_dict_to_pauli_terms,
)
from classiq.execution.jobs import ExecutionJob
from classiq.qmod.builtins.classical_execution_primitives import (
    CARRAY_SEPARATOR,
    ExecutionParams,
)
from classiq.qmod.builtins.structs import PauliTerm, SparsePauliOp
from classiq.qmod.qmod_variable import (
    QmodExpressionCreator,
    create_qvar_from_quantum_type,
)

Hamiltonian = SparsePauliOp
ExecutionParameters = Optional[Union[ExecutionParams, list[ExecutionParams]]]
ParsedExecutionParams = dict[str, Union[float, int]]
ParsedExecutionParameters = Optional[
    Union[ParsedExecutionParams, list[ParsedExecutionParams]]
]


def parse_params(params: ExecutionParams) -> ParsedExecutionParams:
    result = {}
    for key, values in params.items():
        if isinstance(values, list):
            for index, value in enumerate(values):
                new_key = f"{key}{CARRAY_SEPARATOR}{index}"
                result[new_key] = value
        elif isinstance(values, (int, float)):
            result[key] = values
        else:
            raise TypeError("Parameters were provided in un-supported format")
    return result


def _hamiltonian_deprecation_warning(hamiltonian: Any) -> None:
    if isinstance(hamiltonian, list):
        warnings.warn(
            (
                "Parameter type list[PauliTerm] to 'ExecutionSession' methods is "
                "deprecated and will no longer be supported starting on 21/7/2025 "
                "at the earliest. Instead, send a 'SparsePauliOp' (see "
                "https://docs.classiq.io/latest/qmod-reference/language-reference/classical-types/#hamiltonians)."
            ),
            ClassiqDeprecationWarning,
            stacklevel=3,
        )


class ExecutionSession:
    """
    A session for executing a quantum program.
    `ExecutionSession` allows to execute the quantum program with different parameters and operations without the need to re-synthesize the model.
    The session must be closed in order to ensure resources are properly cleaned up. It's recommended to use `ExecutionSession` as a context manager for this purpose. Alternatively, you can directly use the `close` method.

    Attributes:
        quantum_program (QuantumProgram): The quantum program to execute.
        execution_preferences (Optional[ExecutionPreferences]): Execution preferences for the Quantum Program.
    """

    def __init__(
        self,
        quantum_program: QuantumProgram,
        execution_preferences: Optional[ExecutionPreferences] = None,
    ):
        self.program: QuantumProgram = quantum_program
        self.update_execution_preferences(execution_preferences)
        # We never use classical_execution_code in ExecutionSession, and we don't want
        # the conversion route to fail because cmain is expected in some cases
        self.program.model.classical_execution_code = "dummy"

        self._random_seed = self.program.model.execution_preferences.random_seed
        self._rng = random.Random(self._random_seed)  # noqa: S311

        self._async_client = client().async_client()

        self._session_id: str | None = None

    def __enter__(self) -> "ExecutionSession":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """
        Close the session and clean up its resources.
        """
        async_utils.run(self._async_client.aclose())

    def get_session_id(self) -> str:
        if self._session_id is None:
            self._session_id = async_utils.run(
                ApiWrapper.call_create_execution_session(
                    self.program, self._async_client
                )
            )
        return self._session_id

    def _execute(self, primitives_input: PrimitivesInput) -> ExecutionJob:
        primitives_input.random_seed = self._random_seed
        self._random_seed = self._rng.randint(0, 2**32 - 1)
        result = async_utils.run(
            ApiWrapper.call_create_session_job(
                self.get_session_id(), primitives_input, self._async_client
            )
        )
        return ExecutionJob(details=result)

    def update_execution_preferences(
        self, execution_preferences: Optional[ExecutionPreferences]
    ) -> None:
        """
        Update the execution preferences for the session.

        Args:
            execution_preferences: The execution preferences to update.

        Returns:
            None
        """
        if execution_preferences is not None:
            self.program.model.execution_preferences = execution_preferences

    def sample(self, parameters: Optional[ExecutionParams] = None) -> ExecutionDetails:
        """
        Samples the quantum program with the given parameters, if any.

        Args:
            parameters: The values to set for the parameters of the quantum program when sampling. Each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            The result of the sampling.
        """
        job = self.submit_sample(parameters=parameters)
        return job.get_sample_result(_http_client=self._async_client)

    def submit_sample(
        self, parameters: Optional[ExecutionParams] = None
    ) -> ExecutionJob:
        """
        Initiates an execution job with the `sample` primitive.

        This is a non-blocking version of `sample`: it gets the same parameters and initiates the same execution job, but instead
        of waiting for the result, it returns the job object immediately.

        Args:
            parameters: The values to set for the parameters of the quantum program when sampling. Each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            The execution job.
        """
        execution_primitives_input = PrimitivesInput(
            sample=[parse_params(parameters)] if parameters is not None else [{}]
        )
        return self._execute(execution_primitives_input)

    def batch_sample(self, parameters: list[ExecutionParams]) -> list[ExecutionDetails]:
        """
        Samples the quantum program multiple times with the given parameters for each iteration. The number of samples is determined by the length of the parameters list.

        Args:
            parameters: A list of the parameters for each iteration. Each item is a dictionary where each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            List[ExecutionDetails]: The results of all the sampling iterations.
        """
        job = self.submit_batch_sample(parameters=parameters)
        return job.get_batch_sample_result(_http_client=self._async_client)

    def submit_batch_sample(self, parameters: list[ExecutionParams]) -> ExecutionJob:
        """
        Initiates an execution job with the `batch_sample` primitive.

        This is a non-blocking version of `batch_sample`: it gets the same parameters and initiates the same execution job, but instead
        of waiting for the result, it returns the job object immediately.

        Args:
            parameters: A list of the parameters for each iteration. Each item is a dictionary where each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            The execution job.
        """
        execution_primitives_input = PrimitivesInput(
            sample=[parse_params(params) for params in parameters]
        )
        return self._execute(execution_primitives_input)

    def estimate(
        self, hamiltonian: Hamiltonian, parameters: Optional[ExecutionParams] = None
    ) -> EstimationResult:
        """
        Estimates the expectation value of the given Hamiltonian using the quantum program.

        Args:
            hamiltonian: The Hamiltonian to estimate the expectation value of.
            parameters: The values to set for the parameters of the quantum program when estimating.  Each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            EstimationResult: The result of the estimation.
        """
        _hamiltonian_deprecation_warning(hamiltonian)
        job = self.submit_estimate(
            hamiltonian=hamiltonian, parameters=parameters, _check_deprecation=False
        )
        return job.get_estimate_result(_http_client=self._async_client)

    def submit_estimate(
        self,
        hamiltonian: Hamiltonian,
        parameters: Optional[ExecutionParams] = None,
        *,
        _check_deprecation: bool = True,
    ) -> ExecutionJob:
        """
        Initiates an execution job with the `estimate` primitive.

        This is a non-blocking version of `estimate`: it gets the same parameters and initiates the same execution job, but instead
        of waiting for the result, it returns the job object immediately.

        Args:
            hamiltonian: The Hamiltonian to estimate the expectation value of.
            parameters: The values to set for the parameters of the quantum program when estimating.  Each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            The execution job.
        """
        if _check_deprecation:
            _hamiltonian_deprecation_warning(hamiltonian)
        execution_primitives_input = PrimitivesInput(
            estimate=EstimateInput(
                hamiltonian=self._hamiltonian_to_pauli_operator(hamiltonian),
                parameters=(
                    [parse_params(parameters)] if parameters is not None else [{}]
                ),
            )
        )
        return self._execute(execution_primitives_input)

    def batch_estimate(
        self, hamiltonian: Hamiltonian, parameters: list[ExecutionParams]
    ) -> list[EstimationResult]:
        """
        Estimates the expectation value of the given Hamiltonian multiple times using the quantum program, with the given parameters for each iteration. The number of estimations is determined by the length of the parameters list.

        Args:
            hamiltonian: The Hamiltonian to estimate the expectation value of.
            parameters: A list of the parameters for each iteration. Each item is a dictionary where each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            List[EstimationResult]: The results of all the estimation iterations.
        """
        _hamiltonian_deprecation_warning(hamiltonian)
        job = self.submit_batch_estimate(
            hamiltonian=hamiltonian, parameters=parameters, _check_deprecation=False
        )
        return job.get_batch_estimate_result(_http_client=self._async_client)

    def submit_batch_estimate(
        self,
        hamiltonian: Hamiltonian,
        parameters: list[ExecutionParams],
        *,
        _check_deprecation: bool = True,
    ) -> ExecutionJob:
        """
        Initiates an execution job with the `batch_estimate` primitive.

        This is a non-blocking version of `batch_estimate`: it gets the same parameters and initiates the same execution job, but instead
        of waiting for the result, it returns the job object immediately.

        Args:
            hamiltonian: The Hamiltonian to estimate the expectation value of.
            parameters: A list of the parameters for each iteration. Each item is a dictionary where each key should be the name of a parameter in the quantum program (parameters of the main function), and the value should be the value to set for that parameter.

        Returns:
            The execution job.
        """
        if _check_deprecation:
            _hamiltonian_deprecation_warning(hamiltonian)
        execution_primitives_input = PrimitivesInput(
            estimate=EstimateInput(
                hamiltonian=self._hamiltonian_to_pauli_operator(hamiltonian),
                parameters=[parse_params(params) for params in parameters],
            )
        )
        return self._execute(execution_primitives_input)

    def minimize(
        self,
        cost_function: Union[Hamiltonian, QmodExpressionCreator],
        initial_params: ExecutionParams,
        max_iteration: int,
        quantile: float = 1.0,
    ) -> list[tuple[float, ExecutionParams]]:
        """
        Minimizes the given cost function using the quantum program.
        Args:
            cost_function: The cost function to minimize. It can be one of the following:
                - A quantum cost function defined by a Hamiltonian.
                - A classical cost function represented as a callable that returns a Qmod expression.
                  The callable should accept `QVar`s as arguments and use names matching the Model outputs.
            initial_params: The initial parameters for the minimization.
                Only Models with exactly one execution parameter are supported. This parameter must be of type
                `CReal` or `CArray`. The dictionary must contain a single key-value pair, where:
                    - The key is the name of the parameter.
                    - The value is either a float or a list of floats.
            max_iteration: The maximum number of iterations for the minimization.
            quantile: The quantile to use for cost estimation.
        Returns:
            A list of tuples, each containing the estimated cost and the corresponding parameters for that iteration.
            `cost` is a float, and `parameters` is a dictionary matching the execution parameter format.
        """
        _hamiltonian_deprecation_warning(cost_function)
        job = self.submit_minimize(
            cost_function=cost_function,
            initial_params=initial_params,
            max_iteration=max_iteration,
            quantile=quantile,
            _check_deprecation=False,
        )
        result = job.get_minimization_result(_http_client=self._async_client)

        return self._minimize_result_to_result(
            result=result, initial_params=initial_params
        )

    def submit_minimize(
        self,
        cost_function: Union[Hamiltonian, QmodExpressionCreator],
        initial_params: ExecutionParams,
        max_iteration: int,
        quantile: float = 1.0,
        *,
        _check_deprecation: bool = True,
    ) -> ExecutionJob:
        """
        Initiates an execution job with the `minimize` primitive.

        This is a non-blocking version of `minimize`: it gets the same parameters and initiates the same execution job, but instead
        of waiting for the result, it returns the job object immediately.

        Args:
            cost_function: The cost function to minimize. It can be one of the following:
                - A quantum cost function defined by a Hamiltonian.
                - A classical cost function represented as a callable that returns a Qmod expression.
                  The callable should accept `QVar`s as arguments and use names matching the Model outputs.
            initial_params: The initial parameters for the minimization.
                Only Models with exactly one execution parameter are supported. This parameter must be of type
                `CReal` or `CArray`. The dictionary must contain a single key-value pair, where:
                    - The key is the name of the parameter.
                    - The value is either a float or a list of floats.
            max_iteration: The maximum number of iterations for the minimization.
            quantile: The quantile to use for cost estimation.

        Returns:
            The execution job.
        """
        if _check_deprecation:
            _hamiltonian_deprecation_warning(cost_function)
        if len(initial_params) != 1:
            raise ClassiqValueError(
                "The initial parameters must be a dictionary with a single key-value pair."
            )

        _cost_function: Union[PauliOperator, Expression]
        _initial_params = parse_params(initial_params)
        minimize: Union[MinimizeQuantumCostInput, MinimizeClassicalCostInput]
        if callable(cost_function):
            circuit_output_types = self.program.model.circuit_output_types
            _cost_function = self._create_qmod_expression(
                circuit_output_types, cost_function
            )
            minimize = MinimizeClassicalCostInput(
                cost_function=_cost_function,
                initial_params=_initial_params,
                max_iteration=max_iteration,
                quantile=quantile,
            )
        else:
            _cost_function = self._hamiltonian_to_pauli_operator(cost_function)
            minimize = MinimizeQuantumCostInput(
                cost_function=_cost_function,
                initial_params=_initial_params,
                max_iteration=max_iteration,
                quantile=quantile,
            )

        execution_primitives_input = PrimitivesInput(minimize=minimize)
        return self._execute(execution_primitives_input)

    def estimate_cost(
        self,
        cost_func: Callable[[ParsedState], float],
        parameters: Optional[ExecutionParams] = None,
        quantile: float = 1.0,
    ) -> float:
        """
        Estimates circuit cost using a classical cost function.

        Args:
            cost_func: classical circuit sample cost function
            parameters: execution parameters sent to 'sample'
            quantile: drop cost values outside the specified quantile

        Returns:
            cost estimation

        See Also:
            sample
        """
        res = self.sample(parameters)
        return estimate_cost(cost_func, res.parsed_counts, quantile=quantile)

    def set_measured_state_filter(
        self,
        output_name: str,
        condition: Callable,
    ) -> None:
        """
        When simulating on a statevector simulator, emulate the behavior of postprocessing
        by discarding amplitudes for which their states are "undesirable".

        Args:
            output_name: The name of the register to filter
            condition: Filter out values of the statevector for which this callable is False
        """
        if self._session_id is not None:
            raise ClassiqError(
                "set_measured_state_filter must be called before use of the first primitive (sample, estimate...)"
            )

        if output_name not in self.program.model.circuit_outputs:
            raise ClassiqValueError(f"{output_name} is not an output of the model")
        output_type = self.program.model.circuit_output_types[output_name].quantum_types

        legal_bitstrings = []

        if isinstance(output_type, QuantumBit):
            if condition(0):
                legal_bitstrings.append("0")
            if condition(1):
                legal_bitstrings.append("1")
        elif isinstance(output_type, QuantumNumeric):
            size = output_type.size_in_bits
            for i in range(2**size):
                number_string = f"{i:0{size}b}"
                val = number_utils.binary_to_float_or_int(
                    number_string,
                    output_type.fraction_digits_value,
                    output_type.sign_value,
                )
                if condition(val):
                    legal_bitstrings.append(number_string)
            if len(legal_bitstrings) > 1:
                raise NotImplementedError(
                    "Filtering is only supported on a single value per model output"
                )
            if len(legal_bitstrings) == 0:
                raise ClassiqValueError(
                    f"The condition was false for every possible value of {output_name}"
                )
        else:
            raise NotImplementedError(
                "Filtering is only supported on QuantumBit and QuantumNumeric"
            )

        self.program.model.register_filter_bitstrings[output_name] = legal_bitstrings

    @staticmethod
    def _hamiltonian_to_pauli_operator(hamiltonian: Hamiltonian) -> PauliOperator:
        pauli_list: PydanticPauliList
        # FIXME: Remove compatibility (CLS-2912)
        if isinstance(hamiltonian, list):  # type:ignore[unreachable]
            pauli_list = [  # type:ignore[unreachable]
                (
                    pauli_integers_to_str(elem.pauli),
                    cast(complex, elem.coefficient),
                )
                for elem in ExecutionSession._hamiltonian_to_pauli_terms(hamiltonian)
            ]
            return PauliOperator(pauli_list=pauli_list)
        pauli_list = []
        for term in cast(list, hamiltonian.terms):
            paulis = ["I"] * hamiltonian.num_qubits
            for indexed_pauli in term.paulis:
                paulis[len(paulis) - indexed_pauli.index - 1] = indexed_pauli.pauli.name
            pauli_list.append(("".join(paulis), term.coefficient))
        return PauliOperator(pauli_list=pauli_list)

    @staticmethod
    def _create_qmod_expression(
        circuit_output_types: RegisterQuantumTypeDict,
        qmod_expression_creator: QmodExpressionCreator,
    ) -> Expression:
        symbolic_output = {
            name: create_qvar_from_quantum_type(reg.quantum_types, name)
            for name, reg in circuit_output_types.items()
        }
        for name in inspect.signature(qmod_expression_creator).parameters.keys():
            if name not in symbolic_output:
                raise ClassiqValueError(
                    f"The provided QVar: {name} does not match the model outputs: {tuple(circuit_output_types.keys())}. "
                )

        qmod_expression = qmod_expression_creator(**symbolic_output)
        return Expression(expr=str(qmod_expression))

    @staticmethod
    def _hamiltonian_to_pauli_terms(hamiltonian: list) -> list[PauliTerm]:
        if isinstance(hamiltonian[0], PauliTerm):
            return cast(list[PauliTerm], hamiltonian)
        else:
            return _pauli_dict_to_pauli_terms(cast(list[QmodPyStruct], hamiltonian))

    @staticmethod
    def _minimize_result_to_result(
        result: TaggedMinimizeResult, initial_params: ExecutionParams
    ) -> list[tuple[float, ExecutionParams]]:
        param_name = next(iter(initial_params.keys()))
        param_value = initial_params[param_name]
        return [
            (
                res.expectation_value,
                {
                    param_name: (
                        res.parameters[0]
                        if isinstance(param_value, (float, int))
                        else res.parameters
                    )
                },
            )
            for res in result.value
        ]
