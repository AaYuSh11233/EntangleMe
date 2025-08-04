import warnings
from typing import Literal

from classiq.interface.exceptions import ClassiqDeprecationWarning

from classiq.qmod.builtins.functions import RX, H, suzuki_trotter
from classiq.qmod.builtins.operations import repeat
from classiq.qmod.builtins.structs import PauliTerm
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray, CInt, CReal
from classiq.qmod.qmod_variable import QArray, QBit


@qfunc
def qaoa_mixer_layer(b: CReal, target: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the mixer layer for the QAOA algorithm.
    The mixer layer is a sequence of `X` gates applied to each qubit in the target quantum
    array variable.

    Args:
        b: The rotation parameter for the mixer layer.
        target: The target quantum array.
    """
    repeat(target.len, lambda index: RX(b, target[index]))


@qfunc
def qaoa_cost_layer(
    g: CReal, hamiltonian: CArray[PauliTerm], target: QArray[QBit]
) -> None:
    """
    [Qmod Classiq-library function]

    Applies the cost layer to the QAOA model.

    This function integrates the problem-specific cost function into the QAOA model's objective function.
    The cost layer represents the primary objective that the QAOA algorithm seeks to optimize, such as
    minimizing energy or maximizing profit, depending on the application.

    Args:
        g: The rotation parameter for the cost layer (prefactor).
        hamiltonian: The Hamiltonian terms for the QAOA model.
        target: The target quantum array variable.
    """
    with warnings.catch_warnings():  # FIXME: Remove (CLS-2912)
        warnings.simplefilter(
            "ignore", category=ClassiqDeprecationWarning
        )  # FIXME: Remove (CLS-2912)
        suzuki_trotter(hamiltonian, g, 1, 1, target)


@qfunc
def qaoa_layer(
    g: CReal, b: CReal, hamiltonian: CArray[PauliTerm], target: QArray[QBit]
) -> None:
    """
    [Qmod Classiq-library function]

    Applies the QAOA layer, which concatenates the cost layer and the mixer layer.

    The `qaoa_layer` function integrates both the cost and mixer layers, essential components of the
    Quantum Approximate Optimization Algorithm (QAOA). The cost layer encodes the problem's objective,
    while the mixer layer introduces quantum superposition and drives the search across the solution space.

    Args:
           g: The rotation parameter for the cost layer.
           b: The rotation parameter for the mixer layer.
           hamiltonian: The Hamiltonian terms for the QAOA model.
           target: The target quantum array variable.

    """
    qaoa_cost_layer(g, hamiltonian, target)
    qaoa_mixer_layer(b, target)


@qfunc
def qaoa_init(target: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Initializes the QAOA circuit by applying the Hadamard gate to all qubits.

    In the Quantum Approximate Optimization Algorithm (QAOA), the initial state is a uniform superposition
    created by applying the Hadamard gate to each qubit. This function prepares the qubits for the subsequent
    application of the cost and mixer layers by preparing them in an equal superposition state.

    Args:
           target: The target quantum array variable.
    """
    repeat(target.len, lambda index: H(target[index]))


@qfunc
def qaoa_penalty(
    num_qubits: CInt,
    params_list: CArray[CReal],
    hamiltonian: CArray[PauliTerm],
    target: QArray[QBit, Literal["num_qubits"]],
) -> None:
    """
    [Qmod Classiq-library function]

    Applies the penalty layer to the QAOA model.

    This function adds a penalty term to the objective function of the QAOA model to
    enforce certain constraints (e.g., binary or integer variables) during the
    optimization process.

    Args:
        num_qubits: The number of qubits in the quantum circuit.
        params_list The list of QAOA parameters.
        hamiltonian: The Hamiltonian terms for the QAOA model.
        target: The target quantum array variable.
    """
    qaoa_init(target)
    repeat(
        params_list.len / 2,  # type:ignore[arg-type]
        lambda index: qaoa_layer(
            params_list[2 * index], params_list[(2 * index) + 1], hamiltonian, target
        ),
    )
