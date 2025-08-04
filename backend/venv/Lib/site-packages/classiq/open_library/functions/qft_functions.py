from classiq.qmod.builtins.functions.standard_gates import CPHASE, SWAP, H
from classiq.qmod.builtins.operations import repeat
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QArray, QBit
from classiq.qmod.symbolic import pi


@qfunc
def qft_no_swap(qbv: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the Quantum Fourier Transform (QFT) without the swap gates.

    Args:
        qbv: The quantum number to which the QFT is applied.

    """
    repeat(
        qbv.len,
        lambda i: (
            H(qbv[i]),
            repeat(
                qbv.len - i - 1,
                lambda j: CPHASE(
                    theta=pi / (2 ** (j + 1)),
                    ctrl=qbv[i + j + 1],
                    target=qbv[i],
                ),
            ),
        ),
    )


@qfunc
def qft(target: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Performs the Quantum Fourier Transform (QFT) on `target` in-place.
    Implements the following transformation:

    $$
    y_{k} = \\frac{1}{\\sqrt{N}} \\sum_{j=0}^{N-1} x_j e^{2\\pi i \\frac{jk}{N}}
    $$

    Args:
        target: The quantum object to be transformed
    """
    repeat(
        target.len / 2,  # type:ignore[arg-type]
        lambda index: SWAP(target[index], target[(target.len - 1) - index]),
    )
    qft_no_swap(target)
