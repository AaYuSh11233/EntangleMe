from classiq.open_library.functions.grover import grover_operator
from classiq.open_library.functions.qpe import qpe
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QArray, QBit, QNum
from classiq.qmod.quantum_callable import QCallable


@qfunc
def amplitude_estimation(
    oracle: QCallable[QArray[QBit]],
    space_transform: QCallable[QArray[QBit]],
    phase: QNum,
    packed_vars: QArray[QBit],
) -> None:
    """
    [Qmod Classiq-library function]

    Estimate the probability of a state being marked by the operand `oracle` as a "good state."

    The algorithm prepares the state in the `packed_vars` register and estimates the probability of this state being marked by the oracle as a "good state."
    This is done using the Quantum Phase Estimation (QPE) algorithm, where the unitary for QPE is the Grover operator, which is composed of the `oracle` and `space_transform` operators.

    Args:
        oracle: The oracle operator that marks the "good" state. This operator should flip the sign of the amplitude of the "good" state.
        space_transform: The space transform operator (which is known also the state preparation operator), which is first applied to prepare the state before the QPE, and then used inside the Grover operator.
        phase: Assuming this variable starts from the zero state -this variable output holds the $phase=\\theta$ result in the [0,1] domain, which relates to the estimated probability $a$ through $a=\\sin^2(\\pi \\theta)$.
        packed_vars: The variable that holds the state to be estimated. Assumed to be in the zero state at the beginning of the algorithm.
    """
    space_transform(packed_vars)
    qpe(lambda: grover_operator(oracle, space_transform, packed_vars), phase)
