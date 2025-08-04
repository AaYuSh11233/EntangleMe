import warnings
from typing import Literal

import numpy as np
import sympy

from classiq.interface.exceptions import ClassiqDeprecationWarning

from classiq.open_library.functions.utility_functions import (
    apply_to_all,
    hadamard_transform,
)
from classiq.qmod.builtins.functions import (
    CX,
    IDENTITY,
    RY,
    RZ,
    H,
    X,
    inplace_prepare_amplitudes,
)
from classiq.qmod.builtins.operations import (
    allocate,
    control,
    if_,
    inplace_add,
    repeat,
    within_apply,
)
from classiq.qmod.cparam import CArray, CInt, CReal
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import Output, QArray, QBit, QNum
from classiq.qmod.symbolic import (
    acos,
    asin,
    atan,
    exp,
    floor,
    log,
    logical_or,
    max as qmax,
    min as qmin,
    pi,
    sqrt,
)


def _prepare_uniform_trimmed_state_apply_rotation(
    size_lsb: CInt, lsbs_val: CInt, rotation_var: QBit
) -> None:
    # max hold for the case where the value is on the left side
    # the fraction in the sqrt is the wanted amount of probability
    # in the left side divided by the total amount
    RY(
        -2 * (asin(sqrt(qmin((2 ** (size_lsb)) / lsbs_val, 1))) + pi / 4) + pi,
        rotation_var,
    )


@qfunc
def _prepare_uniform_trimmed_state_step(
    size_lsb: CInt, ctrl_val: CInt, lsbs_val: CInt, ctrl_var: QNum, rotation_var: QBit
) -> None:
    if_(
        lsbs_val != 0,  # stop condition
        lambda: control(
            ctrl_var == ctrl_val,
            lambda: _prepare_uniform_trimmed_state_apply_rotation(
                size_lsb, lsbs_val, rotation_var
            ),
        ),
    )


@qfunc
def prepare_uniform_trimmed_state(m: CInt, q: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Initializes a quantum variable in a uniform superposition of the first `m` computational basis states:

    $$
        \\left|\\text{q}\\right\\rangle = \\frac{1}{\\sqrt{m}}\\sum_{i=0}^{m-1}{|i\\rangle}
    $$

    The number of allocated qubits would be $\\left\\lceil\\log_2{m}\\right\\rceil$.
    The function is especially useful when `m` is not a power of 2.

    Args:
        m: The number of states to load in the superposition.
        q: The quantum variable that will receive the initialized state. Must be uninitialized.

    Notes:
        1. If the output variable has been declared with a specific number of qubits, it must match the number of allocated qubits.
        2. The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.
    """
    hadamard_transform(q)

    if_(
        m < 2**q.len,
        # initial step without control
        lambda: _prepare_uniform_trimmed_state_apply_rotation(
            q.len - 1,  # type:ignore[arg-type]
            m,
            q[q.len - 1],
        ),
    )

    repeat(
        qmax(q.len - 1, 0),
        lambda i: _prepare_uniform_trimmed_state_step(
            q.len - i - 2,
            floor(m / (2 ** (q.len - i - 1))),
            m % (2 ** (q.len - i - 1)),
            q[q.len - i - 1 : q.len],
            q[q.len - i - 2],
        ),
    )


@qfunc
def prepare_uniform_interval_state(start: CInt, end: CInt, q: QNum) -> None:
    """
    [Qmod Classiq-library function]

    Initializes a quantum variable in a uniform superposition of the specified interval in the computational basis states:

    $$
        \\left|\\text{q}\\right\\rangle = \\frac{1}{\\sqrt{\\text{end} - \\text{start}}}\\sum_{i=\\text{start}}^{\\text{end}-1}{|i\\rangle}
    $$

    The number of allocated qubits would be $\\left\\lceil\\log_2{\\left(\\text{end}\\right)}\\right\\rceil$.

    Args:
        start: The lower bound of the interval to load (inclusive).
        end: The upper bound of the interval to load (exclusive).
        q: The quantum variable that will receive the initialized state. Must be uninitialized.

    Notes:
        1. If the output variable has been declared with a specific number of qubits, it must match the number of allocated qubits.
        2. The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.
    """
    prepare_uniform_trimmed_state(end - start, q)
    inplace_add(start, q)


@qfunc
def prepare_ghz_state(size: CInt, q: Output[QArray[QBit]]) -> None:
    """
    [Qmod Classiq-library function]

    Initializes a quantum variable in a Greenberger-Horne-Zeilinger (GHZ) state. i.e., a balanced superposition of all ones and all zeros, on an arbitrary number of qubits..

    Args:
        size: The number of qubits in the GHZ state. Must be a positive integer.
        q: The quantum variable that will receive the initialized state. Must be uninitialized.

    Notes:
        The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.


    """

    def inner_lop(step: CInt) -> None:
        repeat(
            count=2**step,
            iteration=lambda control_index: if_(
                condition=control_index + 2**step >= size,
                then=lambda: IDENTITY(q[0]),
                else_=lambda: CX(q[control_index], q[control_index + 2**step]),
            ),
        )

    allocate(size, q)
    H(q[0])
    repeat(floor(log(size - 1, 2)) + 1, inner_lop)  # type:ignore[arg-type]


@qfunc
def prepare_exponential_state(rate: CInt, q: QArray[QBit]) -> None:
    """

    [Qmod Classiq-library function]

    Prepares a quantum state with exponentially decreasing amplitudes. The state is prepared in the computational basis, with the amplitudes of the states decreasing exponentially with the index of the state:

    $$
        P(n) = \\frac{1}{Z} e^{- \\text{rate} \\cdot n}
    $$

    Args:
        rate: The rate of the exponential decay.
        q: The quantum register to prepare.
    """
    repeat(q.len, lambda i: RY(2.0 * atan(exp((-rate * 2.0**i) / 2.0)), q[i]))


@qfunc
def prepare_bell_state(
    state_num: CInt, qpair: Output[QArray[QBit, Literal[2]]]
) -> None:
    """
    [Qmod Classiq-library function]

    Initializes a quantum array of size 2 in one of the four Bell states.

    Args:
        state_num: The number of the Bell state to be prepared. Must be an integer between 0 and 3.
        qpair: The quantum variable that will receive the initialized state. Must be uninitialized.

    Bell States:
        The four Bell states are defined as follows (each state correlates to an integer between 0 and 3 as defined by the `state_num` argument):

        If `state_num` = 0 the function prepares the Bell state:

        $$
            \\left|\\Phi^+\\right\\rangle = \\frac{1}{\\sqrt{2}} \\left( \\left| 00 \\right\\rangle + \\left| 11 \\right\\rangle \\right)
        $$

        If `state_num` = 1 the function prepares the Bell state:

        $$
            \\left|\\Phi^-\\right\\rangle = \\frac{1}{\\sqrt{2}} \\left( \\left| 00 \\right\\rangle - \\left| 11 \\right\\rangle \\right)
        $$

        If `state_num` = 2 the function prepares the Bell state:

        $$
            \\left|\\Psi^+\\right\\rangle = \\frac{1}{\\sqrt{2}} \\left( \\left| 01 \\right\\rangle + \\left| 10 \\right\\rangle \\right)
        $$

        If `state_num` = 3 the function prepares the Bell state:

        $$
            \\left|\\Psi^-\\right\\rangle = \\frac{1}{\\sqrt{2}} \\left( \\left| 01 \\right\\rangle - \\left| 10 \\right\\rangle \\right)
        $$

    Notes:
        The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.


    """
    allocate(qpair)
    if_(logical_or(state_num == 1, state_num == 3), lambda: X(qpair[0]))
    if_(logical_or(state_num == 2, state_num == 3), lambda: X(qpair[1]))
    H(qpair[0])
    CX(qpair[0], qpair[1])


@qfunc
def inplace_prepare_int(value: CInt, target: QNum) -> None:
    """
    [Qmod Classiq-library function]

    This function is **deprecated**. Use in-place-xor assignment statement in the form _target-var_ **^=** _quantum-expression_ or **inplace_xor(**_quantum-expression_**,** _target-var_**)** instead.

    Transitions a quantum variable in the zero state $|0\\rangle$ into the computational basis state $|\\text{value}\\rangle$.
    In the general case, the function performs a bitwise-XOR, i.e. transitions the state $|\\psi\\rangle$ into $|\\psi \\oplus \\text{value}\\rangle$.

    Args:
        value: The value to assign to the quantum variable.
        target: The quantum variable to act upon.

    Note:
        If the value cannot fit into the quantum variable, it is truncated, i.e. treated as the value modulo $2^\\text{target.size}$.
    """
    warnings.warn(
        "Function 'inplace_prepare_int' is deprecated. Use in-place-xor assignment statement in the form '<var> ^= <expression>' or 'inplace_xor(<expression>, <var>)' instead.",
        ClassiqDeprecationWarning,
        stacklevel=1,
    )
    target ^= value


@qfunc
def prepare_int(
    value: CInt,
    out: Output[QNum[Literal["floor(log(value, 2)) + 1"]]],
) -> None:
    """
    [Qmod Classiq-library function]

    This function is **deprecated**. Use assignment statement in the form _target-var_ **|=** _quantum-expression_ or **assign(**_quantum-expression_**,** _target-var_**)** instead.

    Initializes a quantum variable to the computational basis state $|\\text{value}\\rangle$.
    The number of allocated qubits is automatically computed from the value, and is the minimal number required for representation in the computational basis.

    Args:
        value: The value to assign to the quantum variable.
        out: The allocated quantum variable. Must be uninitialized.

    Note:
        If the output variable has been declared with a specific number of qubits, it must match the number of allocated qubits.
    """
    warnings.warn(
        "Function 'prepare_int' is deprecated. Use assignment statement in the form '<var> |= <expression>'  or 'assign(<expression>, <var>)' instead.",
        ClassiqDeprecationWarning,
        stacklevel=1,
    )
    out |= value


def _control_qubit(i: int) -> int:
    if _msb(_graycode(i)) < _msb(_graycode(i + 1)):
        return (_graycode(i) & _graycode(i + 1)).bit_length() - 1
    return (_graycode(i) ^ _graycode(i + 1)).bit_length() - 1


def _graycode(i: int) -> int:
    return i ^ (i >> 1)


def _msb(x: int) -> int:
    """
    largest non zero bit
    """
    if x == 0:
        return 0
    return x.bit_length() - 1


def _classical_hadamard_transform(arr: list[float]) -> np.ndarray:
    return 1 / np.sqrt(len(arr)) * np.array(sympy.fwht(np.array(arr)))


@qfunc
def _load_phases(
    phases: list[float],
    target: QArray[QBit, Literal["log(get_field(phases, 'len'), 2)"]],
) -> None:
    alphas = -2 * _classical_hadamard_transform(phases) / np.sqrt(len(phases))

    for i in range(1, len(alphas) - 1):
        gray = _graycode(i)
        next_gray = _graycode(i + 1)
        RZ(alphas[gray], target[_msb(gray)])
        CX(target[_control_qubit(i)], target[_msb(next_gray)])

    RZ(alphas[_graycode(len(phases) - 1)], target[target.len - 1])


@qfunc
def inplace_prepare_complex_amplitudes(
    magnitudes: CArray[CReal],
    phases: list[float],
    target: QArray[QBit, Literal["log(get_field(magnitudes, 'len'), 2)"]],
) -> None:
    """

    [Qmod Classiq-library function]

    Prepares a quantum state with amplitudes and phases for each state according to the given parameters, in polar representation.
    Expects to act on an initialized zero state $|0\\rangle$.

    Args:
        magnitudes: Absolute values of the state amplitudes.
        phases: phases of the state amplitudes. should be of the same size as `amplitudes`.
        target: The quantum variable to act upon.
    """
    inplace_prepare_amplitudes(magnitudes, 0, target)
    _load_phases(phases, target)


@qfunc
def prepare_complex_amplitudes(
    magnitudes: CArray[CReal],
    phases: list[float],
    out: Output[QArray[QBit, Literal["log(get_field(magnitudes, 'len'), 2)"]]],
) -> None:
    """

    [Qmod Classiq-library function]

    Initializes and prepares a quantum state with amplitudes and phases for each state according to the given parameters, in polar representation.

    Args:
        magnitudes: Absolute values of the state amplitudes.
        phases: phases of the state amplitudes. should be of the same size as `amplitudes`.
        out: The allocated quantum variable. Must be uninitialized.
    """
    allocate(out)
    inplace_prepare_complex_amplitudes(magnitudes, phases, out)


@qfunc
def _dicke_split_cycle_shift(k: int, qvar: QArray[QBit]) -> None:
    """
    internal function, assumes the input is in the form |11..100..0> with up to k ones.
    transforms the state to: sqrt(1/n)*|11..100..0> + sqrt((n-1)/n)*|01..110..0>.
    """
    for i in range(k):
        within_apply(
            lambda i=i: CX(qvar[i + 1], qvar[0]),  # type: ignore[misc]
            lambda i=i: (  # type: ignore[misc]
                control(
                    qvar[0],
                    lambda i=i: RY(2 * acos(sqrt((i + 1) / qvar.len)), qvar[i + 1]),  # type: ignore[misc]
                )
                if i == 0
                else control(
                    qvar[0] & qvar[i],
                    lambda i=i: RY(2 * acos(sqrt((i + 1) / qvar.len)), qvar[i + 1]),  # type: ignore[misc]
                )
            ),
        )


@qfunc
def prepare_dicke_state_unary_input(max_k: int, qvar: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Prepares a Dicke state with a variable number of excitations based on an unary-encoded input.

    The Dicke state is defined to be:

    $$\\mathrm{Dicke}(n, k) = \\frac{1}{\\sqrt{\\binom{n}{k}}} \\sum_{x \\in \\{0,1\\}^n,\\, |x| = k} |x\\rangle$$

    The input register `qvar` is expected to already be initialized in a unary encoding:
    the value k is represented by a string of k ones followed by zeros, e.g., k = 3 -> |11100...0>.
    The function generates a Dicke state with k excitations over a new quantum register,
    where 0 <= k < max_k.

    Args:
        max_k: The maximum number of allowed excitations (upper bound for k).
        qvar: Unary-encoded quantum input register of length >= max_k. Must be pre-initialized.
    """
    if qvar.len > max(1, max_k):
        _dicke_split_cycle_shift(max_k, qvar)
        prepare_dicke_state_unary_input(min(max_k, qvar.len - 2), qvar[1 : qvar.len])


@qfunc
def prepare_dicke_state(k: int, qvar: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Prepares a Dicke state with k excitations over the provided quantum register.

    A Dicke state of n qubits with k excitations is an equal superposition of all basis states
    with exactly k qubits in the $|1\\rangle$ state and $(n - k)$ qubits in the $|0\\rangle$ state.
    For example, $\\mathrm{Dicke}(2, 1) = (|01\\rangle + |10\\rangle) / \\sqrt(2)$.

    In the general case it is defined to be:

    $$\\mathrm{Dicke}(n, k) = \\frac{1}{\\sqrt{\\binom{n}{k}}} \\sum_{x \\in \\{0,1\\}^n,\\, |x| = k} |x\\rangle$$

    Args:
        k: The number of excitations (i.e., number of qubits in state $|1\\rangle$).
        qvar: The quantum register (array of qubits) to initialize. Must be uninitialized and have length >= k.
    """
    if k > 0:
        apply_to_all(X, qvar[0:k])
        prepare_dicke_state_unary_input(k, qvar)


@qfunc
def prepare_basis_state(state: list[bool], arr: Output[QArray]) -> None:
    """
    [Qmod Classiq-library function]

    Initializes a quantum array in the specified basis state.

    Args:
        values: The desired basis state, given as a list of boolean values for each qubit.
        arr: The quantum array to prepare.
    """
    allocate(len(state), arr)
    for idx, value in enumerate(state):
        if value:
            X(arr[idx])
