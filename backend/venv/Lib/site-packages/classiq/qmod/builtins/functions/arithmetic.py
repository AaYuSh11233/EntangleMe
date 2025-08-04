from typing import Literal

from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray, CBool, CReal
from classiq.qmod.qmod_variable import (
    Const,
    Input,
    Output,
    Permutable,
    QArray,
    QBit,
    QNum,
)


@qfunc(external=True)
def unitary(
    elements: CArray[CArray[CReal]],
    target: QArray[QBit, Literal["log(get_field(elements[0], 'len'), 2)"]],
) -> None:
    """
    [Qmod core-library function]

    Applies a unitary matrix on a quantum state.

    Args:
        elements:  A 2d array of complex numbers representing the unitary matrix. This matrix must be unitary.
        target: The quantum state to apply the unitary on. Should be of corresponding size.
    """
    pass


@qfunc(external=True)
def add(
    left: Const[QNum],
    right: Const[QNum],
    result: Permutable[
        Output[
            QNum[
                Literal["result_size"],
                Literal["result_is_signed"],
                Literal["result_fraction_places"],
            ]
        ]
    ],
    result_size: CReal,
    result_is_signed: CBool,
    result_fraction_places: CReal,
) -> None:
    pass


@qfunc(external=True)
def add_inplace_right(
    left: Const[QNum],
    right: Permutable[Input[QNum]],
    result: Permutable[
        Output[
            QNum[
                Literal["result_size"],
                Literal["result_is_signed"],
                Literal["result_fraction_places"],
            ]
        ]
    ],
    result_size: CReal,
    result_is_signed: CBool,
    result_fraction_places: CReal,
) -> None:
    pass


@qfunc(external=True)
def modular_add(left: Const[QArray[QBit]], right: Permutable[QArray[QBit]]) -> None:
    pass


@qfunc(external=True)
def modular_add_constant(left: CReal, right: Permutable[QNum]) -> None:
    pass


@qfunc(external=True)
def integer_xor(left: Const[QArray[QBit]], right: Permutable[QArray[QBit]]) -> None:
    pass


@qfunc(external=True)
def real_xor_constant(left: CReal, right: Permutable[QNum]) -> None:
    pass
