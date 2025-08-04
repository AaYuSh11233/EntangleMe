from typing import Literal

from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray, CReal
from classiq.qmod.qmod_variable import Input, Output, Permutable, QArray, QBit


@qfunc(external=True)
def free(in_: Permutable[Input[QArray[QBit]]]) -> None:
    """
    [Qmod core-library function]

    Releases the qubits allocated to a quantum variable, allowing them to be reused.

    Args:
        in_: The quantum variable that will be freed. Must be initialized before.

    Note:
        This operation does not uncompute the qubits. It is the responsibility of the user to ensure that the qubits are at the zero state before freeing them.
    """
    pass


@qfunc(external=True)
def prepare_state(
    probabilities: CArray[CReal],
    bound: CReal,
    out: Output[QArray[QBit, Literal["log(get_field(probabilities, 'len'), 2)"]]],
) -> None:
    """
    [Qmod core-library function]

    Initializes a quantum variable in a state corresponding to a given probability distribution:

    $$
        \\left|\\text{out}\\right\\rangle = \\sum_{i=0}^{\\text{len(probabilities)}-1} \\sqrt{\\text{probabilities}[i]} \\left|i\\right\\rangle
    $$

    with $i = 0, 1, 2, ..., \\text{len(amplitudes)}-1$ corresponding to computational basis states.

    Args:
        probabilities: The probability distribution to initialize the quantum variable. Must be a valid probability distribution, i.e., a list of non-negative real numbers that sum to 1. Must have a valid length (a power of 2).
        bound: An error bound, expressed as the $L^{2}$ norm between the expected and actual distributions. A larger bound can reduce the circuit size at the expense of accuracy. Must be a positive real number.
        out: The quantum variable that will receive the initialized state. Must be uninitialized.

    Notes:
        1. If the output variable has been declared with a specific number of qubits, the number of qubits formed by the distribution must match the declared number.
        2. The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.
    """
    pass


@qfunc(external=True)
def prepare_amplitudes(
    amplitudes: CArray[CReal],
    bound: CReal,
    out: Output[QArray[QBit, Literal["log(get_field(amplitudes, 'len'), 2)"]]],
) -> None:
    """
    [Qmod core-library function]

    Initializes a quantum variable in a state corresponding to the given amplitudes:

    $$
        \\left|\\text{out}\\right\\rangle = \\sum_{i=0}^{\\text{len(amplitudes)}-1} \\text{amplitudes}[i] \\left|i\\right\\rangle
    $$

    with $i = 0, 1, 2, ..., \\text{len(amplitudes)}-1$ corresponding to computational basis states.

    Args:
        amplitudes: The amplitudes to initialize the quantum variable. Must be a valid real quantum state vector, i.e., the sum of squares should be 1. Must have a valid length (a power of 2).
        bound: An error bound, expressed as the $L^{2}$ norm between the expected and actual distributions. A larger bound can reduce the circuit size at the expense of accuracy. Must be a positive real number.
        out: The quantum variable that will receive the initialized state. Must be uninitialized.

    Notes:
        1. If the output variable has been declared with a specific number of qubits, the number of qubits formed by the distribution must match the declared number.
        2. The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.
    """
    pass


@qfunc(external=True)
def inplace_prepare_state(
    probabilities: CArray[CReal],
    bound: CReal,
    target: QArray[QBit, Literal["log(get_field(probabilities, 'len'), 2)"]],
) -> None:
    """
    [Qmod core-library function]

    Transforms a given quantum variable in the state |0> to the state per the specified probability distribution
    (similar to `prepare_state` but preformed on an initialized variable).

    Args:
        probabilities: The probability distribution corresponding to the quantum variable state. Must be a valid probability distribution, i.e., a list of non-negative real numbers that sum to 1. Must have a valid length (a power of 2).
        bound: An error bound, expressed as the $L^{2}$ norm between the expected and actual distributions. A larger bound can reduce the circuit size at the expense of accuracy. Must be a positive real number.
        target: The quantum variable to act upon.

    This is useful as part of quantum building blocks like the Grover diffuser operator, $\\left|\\psi\\right\\rangle\\left\\langle\\psi\\right| \\left( 2\\left|0\\right\\rangle\\left\\langle0\\right| - \\mathcal{I} \\right)$, where the output state of the oracle is reflected about this state.

    """
    pass


@qfunc(external=True)
def inplace_prepare_amplitudes(
    amplitudes: CArray[CReal],
    bound: CReal,
    target: QArray[QBit, Literal["log(get_field(amplitudes, 'len'), 2)"]],
) -> None:
    """
    [Qmod core-library function]

    Transforms a given quantum variable in the state |0> to the state per the specified amplitudes
    (similar to `prepare_amplitudes` but preformed on an initialized variable).

    Args:
        amplitudes: The amplitudes to initialize the quantum variable. Must be a valid real quantum state vector, i.e., the sum of squares should be 1. Must have a valid length (a power of 2).
        bound: An error bound, expressed as the $L^{2}$ norm between the expected and actual distributions. A larger bound can reduce the circuit size at the expense of accuracy. Must be a positive real number.
        target: The quantum variable to act upon.

    This is useful as part of quantum building blocks like the Grover diffuser operator, $\\left|\\psi\\right\\rangle\\left\\langle\\psi\\right| \\left( 2\\left|0\\right\\rangle\\left\\langle0\\right| - \\mathcal{I} \\right)$, where the output state of the oracle is reflected about this state.

    """
    pass


@qfunc(external=True)
def inplace_prepare_amplitudes_approx(
    amplitudes: CArray[CReal],
    bound: CReal,
    target: QArray[QBit, Literal["log(get_field(amplitudes, 'len'), 2)"]],
) -> None:
    pass


@qfunc(external=True)
def prepare_amplitudes_approx(
    amplitudes: CArray[CReal],
    bound: CReal,
    out: Output[QArray[QBit, Literal["log(get_field(amplitudes, 'len'), 2)"]]],
) -> None:
    pass


@qfunc(external=True)
def inplace_prepare_state_approx(
    probabilities: CArray[CReal],
    bound: CReal,
    target: QArray[QBit, Literal["log(get_field(probabilities, 'len'), 2)"]],
) -> None:
    pass


@qfunc(external=True)
def prepare_state_approx(
    probabilities: CArray[CReal],
    bound: CReal,
    out: Output[QArray[QBit, Literal["log(get_field(probabilities, 'len'), 2)"]]],
) -> None:
    pass
