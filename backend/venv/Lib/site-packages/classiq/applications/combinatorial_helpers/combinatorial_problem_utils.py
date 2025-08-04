import itertools
from functools import partial
from typing import Callable, Union

import numpy as np
import pyomo.environ as pyo

from classiq.interface.combinatorial_optimization.sense import is_maximization
from classiq.interface.combinatorial_optimization.solver_types import QSolver
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.executor.vqe_result import VQESolverResult
from classiq.interface.generator.functions.qmod_python_interface import QmodPyStruct

from classiq.applications.combinatorial_helpers.optimization_model import (
    OptimizationModel,
)
from classiq.applications.combinatorial_helpers.pauli_helpers.pauli_sparsing import (
    SparsePauliOp,
)
from classiq.applications.combinatorial_helpers.pauli_helpers.pauli_utils import (
    pauli_operator_to_hamiltonian,
)
from classiq.applications.combinatorial_helpers.pyomo_utils import (
    add_var_domain_constraints,
    convert_pyomo_to_global_presentation,
    evaluate_objective,
    pyomo_to_qmod_qstruct,
)
from classiq.qmod.builtins.structs import PauliTerm
from classiq.qmod.qmod_variable import QStruct


def compute_qaoa_initial_point(
    hamiltonian: list[PauliTerm],
    repetitions: int,
) -> list[float]:
    coeffs_ising = [pauli_term.coefficient for pauli_term in hamiltonian[1:]]
    # the first coeff is the II...I term
    coeffs_abs = np.abs(coeffs_ising)  # type: ignore[arg-type]
    coeffs_largest = np.sort(coeffs_abs)[len(coeffs_ising) // 2 :]
    operator_norm = np.mean(coeffs_largest)
    time_step = 1 / (2 * operator_norm)  # adapted such that for MAXCUT time_step = 1

    beta_params: np.ndarray = np.linspace(1, 0, repetitions) * time_step
    gamma_params: np.ndarray = np.linspace(0, 1, repetitions) * time_step
    return list(itertools.chain(*zip(gamma_params, beta_params)))


def pyo_model_to_hamiltonian(
    pyo_model: pyo.ConcreteModel, penalty_energy: float
) -> list[PauliTerm]:
    pauli_list = OptimizationModel(
        pyo_model, penalty_energy=penalty_energy, qsolver=QSolver.QAOAPenalty
    ).ising.pauli_list
    return pauli_operator_to_hamiltonian(pauli_list)


def pyo_model_to_qmod_problem(
    pyo_model: pyo.ConcreteModel, penalty_energy: float
) -> tuple[type[QStruct], Callable]:
    with add_var_domain_constraints(pyo_model):
        optimization_model = OptimizationModel(
            pyo_model, penalty_energy=penalty_energy, qsolver=QSolver.QAOAPenalty
        )
        _validate_var_domains(optimization_model)
        qmod_struct = pyomo_to_qmod_qstruct(
            "QAOAVars", optimization_model.vars_not_encoded
        )
        cost_func = partial(
            evaluate_objective, *optimization_model.objective_not_encoded_sympy
        )
        return qmod_struct, cost_func


def _validate_var_domains(model: OptimizationModel) -> None:
    for var in model.vars_not_encoded:
        if (
            isinstance(var.bounds, tuple)
            and len(var.bounds) == 2
            and var.bounds[0] != 0
        ):
            raise ClassiqValueError(
                f"Bounds of variable {var.local_name} must start at 0, got {var.bounds}"
            )


def _str_to_list_int(str_ints: str) -> list[int]:
    return list(map(int, list(str_ints)))


def _decode_vector_str(
    optimization_model: OptimizationModel, vector_str: str
) -> list[int]:
    return optimization_model.decode(
        _str_to_list_int(vector_str[::-1])
    )  # reverse qubit order


def _evaluate_operator(operator: SparsePauliOp, state: Union[list[int], str]) -> float:
    if isinstance(state, list):
        state = "".join([str(x) for x in state])

    cost = 0.0
    for pauli, coeff in zip(operator.paulis, operator.coeffs):
        expectation = 1
        for qubit, pauli_char in enumerate(pauli):
            if pauli_char != "I" and state[qubit] == "1" and pauli_char in ["Z", "Y"]:
                expectation *= -1
        cost += expectation * coeff.real

    return cost


def _eigenstate_to_solution(
    optimization_model: OptimizationModel,
    eigenvector: str,
    probability: float,
    num_shots: int,
) -> QmodPyStruct:
    pauli = optimization_model.get_operator().pauli_list

    paulis = [item[0] for item in pauli]
    coeffs = [item[1] for item in pauli]

    operator = SparsePauliOp(paulis, coeffs)
    cost = _evaluate_operator(operator, eigenvector)

    if is_maximization(optimization_model._model_original):
        cost *= -1

    return {
        "probability": probability,
        "cost": cost,
        "solution": _decode_vector_str(optimization_model, eigenvector),
        "count": round(probability * num_shots),
    }


def _get_combi_solution_histogram(
    optimization_model: OptimizationModel,
    vqe_result: VQESolverResult,
) -> list[QmodPyStruct]:
    if vqe_result.reduced_probabilities is None:
        raise ValueError(
            "reduced_probabilities is optional only for backwards compatibility, but it should always be present here"
        )
    return [
        _eigenstate_to_solution(
            optimization_model, eigenvector, probability, vqe_result.num_shots
        )
        for eigenvector, probability in vqe_result.reduced_probabilities.items()
    ]


def get_optimization_solution_from_pyo(
    pyo_model: pyo.ConcreteModel,
    vqe_result: VQESolverResult,
    penalty_energy: float,
) -> list[QmodPyStruct]:
    converted_pyo_model = convert_pyomo_to_global_presentation(pyo_model)
    optimization_model = OptimizationModel(
        converted_pyo_model, penalty_energy=penalty_energy, qsolver=QSolver.QAOAPenalty
    )
    histogram = _get_combi_solution_histogram(optimization_model, vqe_result)
    histogram.sort(key=lambda x: x["probability"], reverse=True)
    return histogram
