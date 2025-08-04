from classiq.open_library.functions.utility_functions import hadamard_transform
from classiq.qmod.builtins.functions.standard_gates import H, U, X
from classiq.qmod.builtins.operations import (
    allocate,
    bind,
    control,
    invert,
    power,
    within_apply,
)
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CInt
from classiq.qmod.qmod_variable import Const, Permutable, QArray, QBit, QNum
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.symbolic import pi


@qfunc(unchecked=["target"])
def _cond_phase_flip(
    predicate: QCallable[Permutable[QBit]], target: Const[QBit]
) -> None:
    within_apply(lambda: H(target), lambda: predicate(target))


@qfunc
def phase_oracle(
    predicate: QCallable[Const[QArray[QBit]], Permutable[QBit]],
    target: Const[QArray[QBit]],
) -> None:
    """
    [Qmod Classiq-library function]

    Creates a phase oracle operator based on a predicate function.

    Applies a predicate function and marks "good" and "bad" states with a phase flip.
    If the predicate is marked as $\\chi$, and the oracle is marked as $S_{\\chi}$, then:


    $$
    S_{\\chi}\\lvert x \\rangle =
    \\begin{cases}
    -\\lvert x \\rangle & \\text{if } \\chi(x) = 1 \\\\
    \\phantom{-} \\lvert x \\rangle & \\text{if } \\chi(x) = 0
    \\end{cases}
    $$

    Args:
        predicate: A predicate function that takes a QArray of QBits and sets a single QBit |1> if the predicate is true, and |0> otherwise.
        target: The target QArray of QBits to apply the phase oracle to.
    """
    aux = QBit()
    within_apply(
        lambda: [allocate(aux), X(aux)],
        lambda: _cond_phase_flip(lambda x: predicate(target, x), aux),
    )


@qfunc(unchecked=["packed_vars"])
def reflect_about_zero(packed_vars: Const[QArray[QBit]]) -> None:
    """
    [Qmod Classiq-library function]

    Reflects the state about the |0> state (i.e. applies a (-1) phase to all states
    besides the |0> state). Implements the operator $S_0$:

    $$
    \\begin{equation}
    S_0|{x}\\rangle = (-1)^{(x\\ne0)}|{x}\\rangle= (2|{0}\\rangle\\langle{0}|-I)|{x}\\rangle
    \\end{equation}
    $$

    Args:
        packed_vars: The quantum state to reflect.
    """
    msbs: QNum = QNum(size=packed_vars.len - 1)
    lsb = QBit()
    bind(packed_vars, [msbs, lsb])
    within_apply(
        lambda: (X(lsb), H(lsb)),
        lambda: control(msbs == 0, lambda: X(lsb)),
    )
    bind([msbs, lsb], packed_vars)


@qfunc
def grover_diffuser(
    space_transform: QCallable[QArray[QBit]], packed_vars: QArray[QBit]
) -> None:
    """
    [Qmod Classiq-library function]

    Reflects the given state about the A|0> state, where A
    is the `space_transform` parameter. It is defined as:

    $$
    \\begin{equation}
    D = A S_0 A^{\\dagger}
    \\end{equation}
    $$

    where $S_0$ is the reflection about the |0> state (see `reflect_about_zero`).

    Args:
        space_transform: The operator which encodes the axis of reflection.
        packed_vars: The state to which to apply the diffuser.
    """
    within_apply(
        lambda: invert(lambda: space_transform(packed_vars)),
        lambda: reflect_about_zero(packed_vars),
    )


@qfunc
def grover_operator(
    oracle: QCallable[QArray[QBit]],
    space_transform: QCallable[QArray[QBit]],
    packed_vars: QArray[QBit],
) -> None:
    """
    [Qmod Classiq-library function]

    Applies the grover operator, defined by:

    $$
    Q=S_{\\psi_0}S_{\\psi_1}
    $$

    where $S_{\\psi_1}$ is a reflection about marked states, and $S_{\\psi_0}$ is a reflection
    about a given state defined by $|\\psi_0\\rangle = A|0\\rangle$.

    Args:
        oracle: A unitary operator which adds a phase of (-1) to marked states.
        space_transform: The operator which creates $|\\psi_0\\rangle$, the initial state, used by the diffuser to reflect about it.
        packed_vars: The state to which to apply the grover operator.
    """
    oracle(packed_vars)
    grover_diffuser(space_transform, packed_vars)
    U(0, 0, 0, pi, packed_vars[0])


@qfunc
def grover_search(
    reps: CInt, oracle: QCallable[QArray[QBit]], packed_vars: QArray[QBit]
) -> None:
    """
    [Qmod Classiq-library function]

    Applies Grover search algorithm.

    Args:
        reps: Number of repetitions of the grover operator.
        oracle: An oracle that marks the solution.
        packed_vars: Packed form of the variable to apply the grover operator on.

    Returns: None
    """
    hadamard_transform(packed_vars)
    power(
        reps,
        lambda: grover_operator(oracle, hadamard_transform, packed_vars),
    )
