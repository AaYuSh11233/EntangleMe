from typing import Literal

from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CReal
from classiq.qmod.qmod_variable import Const, Permutable, QArray, QBit


@qfunc(external=True)
def H(target: QBit) -> None:
    """
    [Qmod core-library function]

    Performs the Hadamard gate on a qubit.

    This operation is represented by the following matrix:

    $$
    H = \\frac{1}{\\sqrt{2}} \\begin{bmatrix} 1 & 1 \\\\ 1 & -1 \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the Hadamard gate to.
    """
    pass


@qfunc(external=True)
def X(target: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-X gate on a qubit.

    This operation is represented by the following matrix:

    $$
    X = \\begin{bmatrix} 0 & 1 \\\\ 1 & 0 \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the Pauli-X gate to.
    """
    pass


@qfunc(external=True)
def Y(target: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-Y gate on a qubit.

    This operation is represented by the following matrix:

    $$
    Y = \\begin{bmatrix} 0 & -i \\\\ i & 0 \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the Pauli-Y gate to.
    """
    pass


@qfunc(external=True)
def Z(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-Z gate on a qubit.

    This operation is represented by the following matrix:

    $$
    Z = \\begin{bmatrix} 1 & 0 \\\\ 0 & -1 \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the Pauli-Z gate to.
    """
    pass


@qfunc(external=True)
def I(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the identity gate on a qubit.

    This operation is represented by the following matrix:

    $$
    I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the identity gate to.
    """
    pass


@qfunc(external=True)
def S(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the S gate on a qubit.

    This operation is represented by the following matrix:

    $$
    S = \\begin{bmatrix} 1 & 0 \\\\ 0 & i \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the S gate to.
    """
    pass


@qfunc(external=True)
def T(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the T gate on a qubit.

    This operation is represented by the following matrix:

    $$
    T = \\begin{bmatrix} 1 & 0 \\\\ 0 & e^{i\\frac{\\pi}{4}} \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the T gate to.
    """
    pass


@qfunc(external=True)
def SDG(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the S-dagger gate on a qubit.

    This operation is represented by the following matrix:

    $$
    S^\\dagger = \\begin{bmatrix} 1 & 0 \\\\ 0 & -i \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the S-dagger gate to.
    """
    pass


@qfunc(external=True)
def TDG(target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the T-dagger gate on a qubit.

    This operation is represented by the following matrix:

    $$
    T^\\dagger = \\begin{bmatrix} 1 & 0 \\\\ 0 & e^{-i\\frac{\\pi}{4}} \\end{bmatrix}
    $$

    Args:
        target: The qubit to apply the T-dagger gate to.
    """
    pass


@qfunc(external=True)
def PHASE(theta: CReal, target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the phase gate on a qubit.

    This operation is represented by the following matrix:

    $$
    PHASE(\\theta) = \\begin{bmatrix} 1 & 0 \\\\ 0 & e^{i\\theta} \\end{bmatrix}
    $$

    Args:
        theta: The phase angle in radians.
        target: The qubit to apply the phase gate to.
    """
    pass


@qfunc(external=True)
def RX(theta: CReal, target: QBit) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-X rotation gate on a qubit.

    This operation is represented by the following matrix:

    $$
    R_X(\\theta) = e^{-i\\frac{\\theta}{2}X}
     = \\begin{bmatrix} cos(\\frac{\\theta}{2}) & -i sin(\\frac{\\theta}{2}) \\\\ -i sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2}) \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The qubit to apply the Pauli-X rotation gate to.
    """
    pass


@qfunc(external=True)
def RY(theta: CReal, target: QBit) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-Y rotation gate on a qubit.

    This operation is represented by the following matrix:

    $$
    R_Y(\\theta) = e^{-i\\frac{\\theta}{2}Y}
     = \\begin{bmatrix} cos(\\frac{\\theta}{2}) & -sin(\\frac{\\theta}{2}) \\\\ -sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2}) \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The qubit to apply the Pauli-Y rotation gate to.
    """
    pass


@qfunc(external=True)
def RZ(theta: CReal, target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Performs the Pauli-Z rotation gate on a qubit.

    This operation is represented by the following matrix:

    $$
    R_Z(\\theta) = e^{-i\\frac{\\theta}{2}Z}
     = \\begin{bmatrix} e^{-i\\frac{\\theta}{2}} & 0 \\\\ 0 & e^{i\\frac{\\theta}{2}} \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The qubit to apply the Pauli-Z rotation gate to.
    """
    pass


@qfunc(external=True)
def R(theta: CReal, phi: CReal, target: QBit) -> None:
    """
    [Qmod core-library function]

    Performs a rotation of $\\theta$ around the $cos(\\phi)\\hat{x} + sin(\\phi)\\hat{y}$ axis on a qubit.

    This operation is represented by the following matrix:

    $$
    R(\\theta, \\phi) = e^{-i \\frac{\\theta}{2} (cos(\\phi)X + sin(\\phi)Y)}
     = \\begin{bmatrix} cos(\\frac{\\theta}{2}) & -i e^{-i\\phi} sin(\\frac{\\theta}{2}) \\\\ -i e^{i\\phi} sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2}) \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        phi: The phase angle in radians.
        target: The qubit to apply the general single-qubit rotation gate to.
    """
    pass


@qfunc(external=True)
def RXX(theta: CReal, target: QArray[QBit, Literal[2]]) -> None:
    """
    [Qmod core-library function]

    Performs the XX rotation gate on a pair of qubits.

    This operation is represented by the following matrix:

    $$
    R_{XX}(\\theta) = e^{-i\\frac{\\theta}{2}X \\otimes X}
     = \\begin{bmatrix} cos(\\frac{\\theta}{2}) & 0 & 0 & -i sin(\\frac{\\theta}{2}) \\\\ 0 & cos(\\frac{\\theta}{2}) & -i sin(\\frac{\\theta}{2}) & 0 \\\\ 0 & -i sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2}) & 0 \\\\ -i sin(\\frac{\\theta}{2}) & 0 & 0 & cos(\\frac{\\theta}{2}) \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The pair of qubits to apply the XX rotation gate to.
    """
    pass


@qfunc(external=True)
def RYY(theta: CReal, target: QArray[QBit, Literal[2]]) -> None:
    """
    [Qmod core-library function]

    Performs the YY rotation gate on a pair of qubits.

    This operation is represented by the following matrix:

    $$
    R_{YY}(\\theta) = e^{-i\\frac{\\theta}{2}Y \\otimes Y}
     = \\begin{bmatrix} cos(\\frac{\\theta}{2}) & 0 & 0 & -sin(\\frac{\\theta}{2}) \\\\ 0 & cos(\\frac{\\theta}{2}) & sin(\\frac{\\theta}{2}) & 0 \\\\ 0 & sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2}) & 0 \\\\ -sin(\\frac{\\theta}{2}) & 0 & 0 & cos(\\frac{\\theta}{2}) \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The pair of qubits to apply the YY rotation gate to.
    """
    pass


@qfunc(external=True)
def RZZ(theta: CReal, target: Const[QArray[QBit, Literal[2]]]) -> None:
    """
    [Qmod core-library function]

    Performs the ZZ rotation gate on a pair of qubits.

    This operation is represented by the following matrix:

    $$
    R_{ZZ}(\\theta) = e^{-i\\frac{\\theta}{2}Z \\otimes Z}
     = \\begin{bmatrix} e^{-i\\frac{\\theta}{2}} & 0 & 0 & 0 \\\\ 0 & e^{i\\frac{\\theta}{2}} & 0 & 0 \\\\ 0 & 0 & e^{i\\frac{\\theta}{2}} & 0 \\\\ 0 & 0 & 0 & e^{-i\\frac{\\theta}{2}} \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        target: The pair of qubits to apply the ZZ rotation gate to.
    """
    pass


@qfunc(external=True)
def CH(ctrl: Const[QBit], target: QBit) -> None:
    """
    [Qmod core-library function]

    Applies the Hadamard gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CH = \\frac{1}{\\sqrt{2}} \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 1 & 1 \\\\
    0 & 0 & 1 & -1
    \\end{bmatrix}
    $$

    Args:
        ctrl: The control qubit.
        target: The qubit to apply the Hadamard gate on.
    """
    pass


@qfunc(external=True)
def CX(ctrl: Const[QBit], target: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the Pauli-X gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CX = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 0 & 1 \\\\
    0 & 0 & 1 & 0
    \\end{bmatrix}
    $$

    Args:
        ctrl: The control qubit.
        target: The qubit to apply the Pauli-X gate on.
    """
    pass


@qfunc(external=True)
def CY(ctrl: Const[QBit], target: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the Pauli-Y gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CY = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 0 & -i \\\\
    0 & 0 & i & 0
    \\end{bmatrix}
    $$

    Args:
        ctrl: The control qubit.
        target: The qubit to apply the Pauli-Y gate on.
    """
    pass


@qfunc(external=True)
def CZ(ctrl: Const[QBit], target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the Pauli-Z gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CZ = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 1 & 0 \\\\
    0 & 0 & 0 & -1
    \\end{bmatrix}
    $$

    Args:
        ctrl: The control qubit.
        target: The qubit to apply the Pauli-Z gate on.
    """
    pass


@qfunc(external=True)
def CRX(theta: CReal, ctrl: Const[QBit], target: QBit) -> None:
    """
    [Qmod core-library function]

    Applies the RX gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CRX = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & cos(\\frac{\\theta}{2}) & -i*sin(\\frac{\\theta}{2}) \\\\
    0 & 0 & -i*sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2})
    \\end{bmatrix}
    $$

    Args:
        theta: The rotation angle in radians.
        ctrl: The control qubit.
        target: The qubit to apply the RX gate on.
    """
    pass


@qfunc(external=True)
def CRY(theta: CReal, ctrl: Const[QBit], target: QBit) -> None:
    """
    [Qmod core-library function]

    Applies the RY gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CRY = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & cos(\\frac{\\theta}{2}) & -sin(\\frac{\\theta}{2}) \\\\
    0 & 0 & sin(\\frac{\\theta}{2}) & cos(\\frac{\\theta}{2})
    \\end{bmatrix}
    $$

    Args:
        theta (CReal): The rotation angle in radians.
        ctrl (QBit): The control qubit.
        target (QBit): The qubit to apply the RY gate on.
    """
    pass


@qfunc(external=True)
def CRZ(theta: CReal, ctrl: Const[QBit], target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the RZ gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CRZ = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & e^{-i\\frac{\\theta}{2}} & 0 \\\\
    0 & 0 & 0 & e^{i\\frac{\\theta}{2}}
    \\end{bmatrix}
    $$

    Args:
        theta (CReal): The rotation angle in radians.
        ctrl (QBit): The control qubit.
        target (QBit): The qubit to apply the RZ gate on.
    """
    pass


@qfunc(external=True)
def CPHASE(theta: CReal, ctrl: Const[QBit], target: Const[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the PHASE gate to the target qubit, conditioned on the control qubit.

    This operation is represented by the following matrix:

    $$
    CPHASE = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 1 & 0 \\\\
    0 & 0 & 0 & e^{i\\theta}
    \\end{bmatrix}
    $$

    Args:
        theta (CReal): The rotation angle in radians.
        ctrl (QBit): The control qubit.
        target (QBit): The qubit to apply the PHASE gate on.
    """
    pass


@qfunc(external=True)
def SWAP(qbit0: Permutable[QBit], qbit1: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Swaps the states of two qubits.

    This operation is represented by the following matrix:

    $$
    SWAP = \\begin{bmatrix}
    1 & 0 & 0 & 0 \\\\
    0 & 0 & 1 & 0 \\\\
    0 & 1 & 0 & 0 \\\\
    0 & 0 & 0 & 1
    \\end{bmatrix}
    $$

    Args:
        qbit0 (QBit): The first qubit.
        qbit1 (QBit): The second qubit.
    """
    pass


@qfunc(external=True)
def IDENTITY(target: Const[QArray[QBit]]) -> None:
    """
    [Qmod core-library function]

    Does nothing.

    This operation is represented by the following matrix:

    $$
    IDENTITY = {\\begin{bmatrix}
    1 & 0 \\\\
    0 & 1
    \\end{bmatrix}} ^{\\otimes n}
    $$

    Args:
        target (QArray[QBit]): The qubits to apply the IDENTITY gate on.
    """
    pass


@qfunc(external=True)
def U(theta: CReal, phi: CReal, lam: CReal, gam: CReal, target: QBit) -> None:
    """
    [Qmod core-library function]

    Performs a general single-qubit unitary gate that applies phase and rotation with three Euler angles on a qubit.

    This operation is represented by the following matrix:

    $$
    U(\\theta, \\phi, \\lambda, \\gamma) = e^{i \\gamma}
    \\begin{bmatrix}
    cos(\\theta/2) & -e^{i(\\lambda)} sin(\\theta/2) \\\\
    e^{i\\phi} sin(\\theta/2) & e^{i(\\phi + \\lambda)} cos(\\theta/2)
    \\end{bmatrix}
    $$

    Args:
        theta (CReal): The first Euler angle in radians.
        phi (CReal): The second Euler angle in radians.
        lam (CReal): The third Euler angle in radians.
        gam (CReal): The global phase angle in radians.
        target (QBit): The qubit to apply the general single-qubit unitary gate to.
    """
    pass


@qfunc(external=True)
def CCX(ctrl: Const[QArray[QBit, Literal[2]]], target: Permutable[QBit]) -> None:
    """
    [Qmod core-library function]

    Applies the Pauli-X gate to the target qubit, conditioned on the two control qubits (Toffoli).

    This operation is represented by the following matrix:

    $$
    CCX = \\begin{bmatrix}
    1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\\\
    0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\\\
    0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\\\
    0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\\\
    0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\\\
    0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\\\
    0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\\\
    0 & 0 & 0 & 0 & 0 & 0 & 1 & 0
    \\end{bmatrix}
    $$

    Args:
        ctrl (QArray[QBit, Literal[2]]): The control qubits.
        target (QBit): The qubit to apply the conditioned Pauli-X gate on.
    """
    pass
