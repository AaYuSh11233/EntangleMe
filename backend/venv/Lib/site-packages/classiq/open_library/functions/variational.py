from classiq.qmod.builtins.functions.standard_gates import RX, RY, RZ
from classiq.qmod.builtins.operations import allocate, repeat
from classiq.qmod.cparam import CReal
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray
from classiq.qmod.qmod_variable import Output, QArray, QBit
from classiq.qmod.symbolic import ceiling, floor, pi


@qfunc
def encode_in_angle(data: CArray[CReal], qba: Output[QArray[QBit]]) -> None:
    """
    [Qmod Classiq-library function]

    Creates an angle encoding of n data points on n qubits.

    Applies RY($\\pi$data[i]) on qba[i].

    Args:
        data: A classical array representing the data to encode.
        qba: The array of qubits on which the data is encoded.
    """
    allocate(data.len, qba)
    repeat(
        count=data.len,
        iteration=lambda index: RY(pi * data[index], qba[index]),
    )


@qfunc
def encode_on_bloch(data: CArray[CReal], qba: Output[QArray]) -> None:
    """
    [Qmod Classiq-library function]

    Creates a dense angle encoding of n data points on n//2 qubits.

    Encodes pairs of data points on a Bloch sphere, via RX($\\pi$data[2*i])RZ($\\pi$data[2*i+1]) on qba[i].
    If the length of the data is odd then RX($\\pi$data[i]) is applied on the last qubit.

    Args:
        data: A classical array representing the data to encode.
        qba: The QArray of QBits on which the data is encoded.
    """
    allocate(ceiling(data.len / 2), qba)
    repeat(
        count=ceiling(data.len / 2),
        iteration=lambda index: RX(pi * data[2 * index], qba[index]),
    )
    repeat(
        count=floor(data.len / 2),
        iteration=lambda index: RZ(pi * data[2 * index + 1], qba[index]),
    )
