from classiq.open_library.functions.qft_functions import qft
from classiq.open_library.functions.utility_functions import apply_to_all
from classiq.qmod.builtins.functions.standard_gates import H
from classiq.qmod.builtins.operations import control, invert, power, repeat
from classiq.qmod.cparam import CInt
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QArray, QBit, QNum
from classiq.qmod.quantum_callable import QCallable


@qfunc
def qpe_flexible(unitary_with_power: QCallable[CInt], phase: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Implements the Quantum Phase Estimation (QPE) algorithm,  which estimates the phase (eigenvalue) associated with an eigenstate of a given unitary operator $U$.
    This is a flexible version that allows the user to provide a callable that generates the unitary operator $U^k$ for a given integer $k$, offering greater flexibility in handling different quantum circuits using some powering rule.

    Args:
        unitary_with_power: A callable that returns the unitary operator $U^k$ given an integer $k$. This callable is used to control the application of powers of the unitary operator.
        phase: The quantum variable that represents the estimated phase (eigenvalue), assuming initialized to zero.
    """
    apply_to_all(H, phase)

    repeat(
        count=phase.len,
        iteration=lambda index: control(
            ctrl=phase[index], stmt_block=lambda: unitary_with_power(2**index)
        ),
    )

    invert(lambda: qft(phase))


@qfunc
def qpe(unitary: QCallable, phase: QNum) -> None:
    """
    [Qmod Classiq-library function]

    Implements the standard Quantum Phase Estimation (QPE) algorithm, which estimates the phase (eigenvalue) associated with an eigenstate of a given unitary operator $U$.

    Args:
        unitary: A callable representing the unitary operator $U$, whose eigenvalue is to be estimated.
        phase: The quantum variable that represents the estimated phase (eigenvalue), assuming initialized to zero.
    """
    qpe_flexible(unitary_with_power=lambda k: power(k, unitary), phase=phase)
