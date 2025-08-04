"""Classiq SDK."""

from classiq.interface._version import VERSION as _VERSION
from classiq.interface.generator.application_apis import *  # noqa: F403
from classiq.interface.generator.arith.register_user_input import (
    RegisterArithmeticInfo,
    RegisterUserInput,
)
from classiq.interface.generator.control_state import ControlState
from classiq.interface.generator.functions import *  # noqa: F403
from classiq.interface.generator.model import *  # noqa: F403
from classiq.interface.generator.model import __all__ as _md_all
from classiq.interface.generator.quantum_program import QuantumProgram

from classiq import applications, execution, synthesis
from classiq._internals import logger
from classiq._internals.async_utils import (
    enable_jupyter_notebook,
    is_notebook as _is_notebook,
)
from classiq._internals.authentication.authentication import authenticate
from classiq._internals.client import configure
from classiq._internals.config import Configuration
from classiq._internals.help import open_help
from classiq.analyzer import Analyzer
from classiq.applications.chemistry import (
    construct_chemistry_model,
    molecule_problem_to_qmod,
)
from classiq.applications.combinatorial_optimization import (
    CombinatorialProblem,
    compute_qaoa_initial_point,
    construct_combinatorial_optimization_model,
    execute_qaoa,
    pyo_model_to_hamiltonian,
)
from classiq.applications.hamiltonian.pauli_decomposition import (
    hamiltonian_to_matrix,
    matrix_to_hamiltonian,
    matrix_to_pauli_operator,
)
from classiq.execution import *  # noqa: F403
from classiq.execution import __all__ as _execution_all
from classiq.executor import (
    execute,
    execute_async,
    set_quantum_program_execution_preferences,
)
from classiq.open_library import *  # noqa: F403
from classiq.open_library import __all__ as _open_library_all
from classiq.qmod import *  # noqa: F403
from classiq.qmod import __all__ as _qmod_all
from classiq.quantum_program import ExecutionParams, assign_parameters, transpile
from classiq.synthesis import (
    quantum_program_from_qasm,
    quantum_program_from_qasm_async,
    set_constraints,
    set_execution_preferences,
    set_preferences,
    show,
    synthesize,
    synthesize_async,
    update_constraints,
    update_execution_preferences,
    update_preferences,
)

_application_constructors_all = [
    "construct_combinatorial_optimization_model",
    "construct_chemistry_model",
    "molecule_problem_to_qmod",
]

__version__ = _VERSION

if _is_notebook():
    enable_jupyter_notebook()

_sub_modules = [
    "analyzer",
    "applications",
    "execution",
    "open_help",
    "qmod",
    "synthesis",
]

__all__ = (
    [
        "RegisterUserInput",
        "RegisterArithmeticInfo",
        "ControlState",
        "Analyzer",
        "ExecutionParams",
        "QuantumProgram",
        "authenticate",
        "assign_parameters",
        "synthesize",
        "synthesize_async",
        "execute",
        "execute_async",
        "set_preferences",
        "set_constraints",
        "set_execution_preferences",
        "transpile",
        "update_preferences",
        "update_constraints",
        "update_execution_preferences",
        "set_quantum_program_execution_preferences",
        "show",
        "hamiltonian_to_matrix",
        "matrix_to_hamiltonian",
        "matrix_to_pauli_operator",
        "quantum_program_from_qasm",
        "quantum_program_from_qasm_async",
    ]
    + _md_all
    + _sub_modules
    + _application_constructors_all
    + _qmod_all
    + _execution_all
    + _open_library_all
)


def __dir__() -> list[str]:
    return __all__
