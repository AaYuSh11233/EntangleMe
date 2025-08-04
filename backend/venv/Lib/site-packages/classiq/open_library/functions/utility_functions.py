import warnings
from typing import Annotated

from classiq.interface.exceptions import ClassiqDeprecationWarning

from classiq.open_library.functions.qft_functions import qft
from classiq.qmod.builtins.functions.standard_gates import PHASE, H
from classiq.qmod.builtins.operations import bind, repeat, within_apply
from classiq.qmod.cparam import CInt
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QArray, QBit, QCallable, QNum
from classiq.qmod.quantum_callable import QCallableList
from classiq.qmod.symbolic import pi


@qfunc
def apply_to_all(
    gate_operand: QCallable[Annotated[QBit, "target"]], target: QArray[QBit]
) -> None:
    """
    [Qmod Classiq-library function]

    Applies the single-qubit operand `gate_operand` to each qubit in the qubit
    array `target`.

    Args:
        gate_operand: The single-qubit gate to apply to each qubit in the array.
        target: The qubit array to apply the gate to.
    """
    repeat(target.len, lambda index: gate_operand(target[index]))


@qfunc
def hadamard_transform(target: QArray[QBit]) -> None:
    r"""
    [Qmod Classiq-library function]

    Applies Hadamard transform to the target qubits.

    Corresponds to the braket notation:

    $$
     H^{\otimes n} |x\rangle = \frac{1}{\sqrt{2^n}} \sum_{y=0}^{2^n - 1} (-1)^{x \\cdot y} |y\rangle
    $$

    Args:
        target:  qubits to apply to Hadamard transform to.

    """
    repeat(target.len, lambda index: H(target[index]))


@qfunc
def switch(selector: CInt, cases: QCallableList) -> None:
    cases[selector]()


@qfunc
def modular_increment(a: CInt, x: QNum) -> None:
    """
    [Qmod Classiq-library function]

    Adds $a$ to $x$ modulo the range of $x$, assumed that $x$ is a non-negative integer and $a$ is an integer.
    Mathematically it is described as:

    $$
        x = (x+a)\\ \\mod \\ 2^{x.size}-1
    $$

    Args:
        a: A classical integer to be added to x.
        x: A quantum number that is assumed to be non-negative integer.

    """
    warnings.warn(
        "Function 'modular_increment' is deprecated. Use in-place-add statement in the form '<var> += <expression>'  or 'inplace_add(<expression>, <var>)' instead.",
        ClassiqDeprecationWarning,
        stacklevel=1,
    )
    array_cast: QArray = QArray()
    within_apply(
        lambda: (
            bind(x, array_cast),
            qft(array_cast),
        ),
        lambda: repeat(
            x.size, lambda i: PHASE(a * 2 * pi * 2**i / (2**x.size), array_cast[i])
        ),
    )
