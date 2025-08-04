import math
import re
from typing import Callable, Optional, cast

import numpy as np
import pandas as pd
import pyomo.core as pyo
import scipy

from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.executor.result import ExecutionDetails
from classiq.interface.model.model import SerializedModel

from classiq import Constraints, Preferences, QuantumProgram
from classiq.applications.combinatorial_helpers.combinatorial_problem_utils import (
    pyo_model_to_qmod_problem,
)
from classiq.execution import ExecutionSession
from classiq.open_library.functions.utility_functions import (
    apply_to_all,
    hadamard_transform,
)
from classiq.qmod.builtins.functions import RX
from classiq.qmod.builtins.operations import allocate, phase, repeat
from classiq.qmod.cparam import CReal
from classiq.qmod.create_model_function import create_model
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray
from classiq.qmod.qmod_variable import Output, QVar
from classiq.synthesis import synthesize


class CombinatorialProblem:
    def __init__(
        self,
        pyo_model: pyo.ConcreteModel,
        num_layers: int,
        penalty_factor: int = 1,
    ):
        self.problem_vars_, self.cost_func = pyo_model_to_qmod_problem(
            pyo_model, penalty_factor
        )
        self.num_layers_ = num_layers
        self.model_ = None
        self.qprog_ = None
        self._es: ExecutionSession | None = None
        self._optimized_params: list[float] | None = None
        self.params_trace_: list[np.ndarray] = []
        self._cost_trace: list[float] = []

    @property
    def cost_trace(self) -> list[float]:
        return self._cost_trace

    @property
    def params_trace(self) -> list[np.ndarray]:
        return self.params_trace_

    @property
    def optimized_params(self) -> list[float]:
        return self._optimized_params  # type:ignore[return-value]

    def get_model(
        self,
        constraints: Optional[Constraints] = None,
        preferences: Optional[Preferences] = None,
    ) -> SerializedModel:
        @qfunc
        def main(
            params: CArray[CReal, self.num_layers_ * 2],  # type:ignore[valid-type]
            v: Output[self.problem_vars_],  # type:ignore[name-defined]
        ) -> None:
            allocate(v.size, v)
            hadamard_transform(v)
            repeat(
                self.num_layers_,
                lambda i: [
                    phase(-self.cost_func(v), params[i]),
                    apply_to_all(lambda q: RX(params[self.num_layers_ + i], q), v),
                ],
            )

        self.model_ = create_model(
            main, constraints=constraints, preferences=preferences
        )  # type:ignore[assignment]
        return self.model_  # type:ignore[return-value]

    def get_qprog(self) -> QuantumProgram:
        if self.model_ is None:
            self.get_model()
        self.qprog_ = synthesize(self.model_)  # type:ignore[assignment,arg-type]
        return self.qprog_  # type:ignore[return-value]

    def optimize(
        self,
        execution_preferences: Optional[ExecutionPreferences] = None,
        maxiter: int = 20,
        quantile: float = 1.0,
    ) -> list[float]:
        if self.qprog_ is None:
            self.get_qprog()
        _es = ExecutionSession(
            self.qprog_, execution_preferences  # type:ignore[arg-type]
        )
        initial_params = (
            np.concatenate(
                (
                    np.linspace(1 / self.num_layers_, 1, self.num_layers_),
                    np.linspace(1, 1 / self.num_layers_, self.num_layers_),
                )
            )
            * math.pi
        )
        result = _es.minimize(
            lambda v: self.cost_func(v),  # type:ignore[arg-type]
            {"params": initial_params.tolist()},
            maxiter,
            quantile,
        )
        _optimized_params = cast(list[float], result[-1][1]["params"])
        self._optimized_params = _optimized_params
        self._cost_trace = [cost for cost, _ in result]
        self._es = _es
        return _optimized_params

    def sample_uniform(self) -> pd.DataFrame:
        return self.sample([0] * self.num_layers_ * 2)

    def sample(self, params: list) -> pd.DataFrame:
        assert self._es is not None
        res = self._es.sample({"params": params})
        parsed_result = [
            {
                "solution": {
                    key: value
                    for key, value in sampled.state["v"].items()
                    if not re.match(".*_slack_var_.*", key)
                },
                "probability": sampled.shots / res.num_shots,  # type:ignore[operator]
                "cost": self.cost_func(sampled.state["v"]),
            }
            for sampled in res.parsed_counts
        ]
        return pd.DataFrame.from_records(parsed_result)

    def teardown(self) -> None:
        if self._es is not None:
            self._es.close()


def execute_qaoa(
    problem_vars: type[QVar],
    cost_func: Callable,
    num_layers: int,
    maxiter: int,
    execution_preferences: Optional[ExecutionPreferences] = None,
) -> tuple[SerializedModel, QuantumProgram, ExecutionDetails]:
    """
    Implements a simple QAOA algorithm, including the creation and synthesis of the QAOA
    ansatz and the classical optimization loop.

    Args:
        problem_vars: the quantum type (scalar, array, or struct) of the problem variable(s)
        cost_func: the arithmetic expression that evaluates the cost given an instance of the problem_vars type
        num_layers: the number of layers of the QAOA ansatz
        maxiter: the maximum number of iterations for the classical optimization loop
        execution_preferences: the execution settings for running the QAOA ansatz

    Returns:
        a tuple containing the model of the QAOA ansatz, the corresponding synthesized quantum program,
        and the result of the execution with the optimized parameters
    """

    @qfunc
    def main(
        params: CArray[CReal, num_layers * 2],  # type:ignore[valid-type]
        v: Output[problem_vars],  # type:ignore[valid-type]
    ) -> None:
        allocate(v.size, v)  # type:ignore[attr-defined]
        hadamard_transform(v)
        repeat(
            num_layers,
            lambda i: [
                phase(-cost_func(v), params[i]),
                apply_to_all(lambda q: RX(params[num_layers + i], q), v),
            ],
        )

    model = main.create_model().get_model()
    qprog = synthesize(model)

    with ExecutionSession(qprog, execution_preferences) as es:
        initial_params = (
            np.concatenate(
                (np.linspace(0, 1, num_layers), np.linspace(1, 0, num_layers))
            )
            * math.pi
        )
        final_params = scipy.optimize.minimize(
            lambda params: es.estimate_cost(
                lambda state: cost_func(state["v"]),
                {"params": params.tolist()},
            ),
            x0=initial_params,
            method="COBYLA",
            options={"maxiter": maxiter},
        ).x.tolist()
        result = es.sample({"params": final_params})

    return model, qprog, result
