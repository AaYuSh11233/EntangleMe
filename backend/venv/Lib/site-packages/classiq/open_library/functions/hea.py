from typing import Annotated, Literal

from classiq.qmod.builtins.operations import if_, repeat
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CArray, CInt, CReal
from classiq.qmod.qmod_variable import QArray, QBit
from classiq.qmod.quantum_callable import QCallableList
from classiq.qmod.symbolic import floor, sum


@qfunc
def full_hea(
    num_qubits: CInt,
    is_parametrized: CArray[CInt],
    angle_params: CArray[CReal],
    connectivity_map: CArray[CArray[CInt]],
    reps: CInt,
    operands_1qubit: QCallableList[Annotated[CReal, "angle"], Annotated[QBit, "q"]],
    operands_2qubit: QCallableList[
        Annotated[CReal, "angle"], Annotated[QBit, "q1"], Annotated[QBit, "q2"]
    ],
    x: QArray[QBit, Literal["num_qubits"]],
) -> None:
    """
    [Qmod Classiq-library function]

    Implements an ansatz on a qubit array `x` with the given 1-qubit and 2-qubit operations.

    The number of ansatz layers is given in argument `reps`.
    Each layer applies the 1-qubit operands in `operands_1qubit` to all the qubits in `x`.
    Next, it applies the 2-qubit operands in `operands_2qubit` to qubits (i, j) for each
    pair of indices (i, j) in `connectivity_map`.

    The list `is_parametrized` specifies whether the operands in `operands_1qubit` and
    `operands_2qubit` are parametric (expect a classical argument).
    `is_parametrized` is a list of flags (0 and 1 integers) of length
    `len(operands_1qubit) + len(operands_2qubit)`.
    The first `len(operands_1qubit)` flags refer to the `operands_1qubit` operands and
    the next `len(operands_2qubit)` flags refer to the `operands_2qubit` operands.

    The classical arguments to the parametric operands are given in argument
    `angle_params`.
    `angle_params` concatenates a set of arguments for each ansatz layer.
    Each set contains an argument for each qubit in `x` times the number
    of parametric operands in `operands_1qubit`.
    These are followed by an argument for each mapping pair in `connectivity_map` times
    the number of parametric operands in `operands_2qubit`.

    Args:
        num_qubits: The length of qubit array x
        is_parametrized: A list of 0 and 1 flags
        angle_params A list of arguments to gate
        connectivity_map: A list of pairs of qubit indices
        reps: The number of ansatz layers
        operands_1qubit: A list of operations on a single qubit
        operands_2qubit: A list of operations on two qubits
        x: The quantum object to be transformed by the ansatz
    """
    repeat(
        reps,
        lambda r: [
            repeat(
                operands_1qubit.len,
                lambda i1: repeat(
                    num_qubits,
                    lambda index: if_(
                        condition=is_parametrized[i1] == 1,
                        then=lambda: operands_1qubit[i1](
                            angle_params[
                                sum(is_parametrized[0:i1])  # type:ignore[index]
                                + floor((angle_params.len / reps) * r)
                                + index
                            ],
                            x[index],
                        ),
                        else_=lambda: operands_1qubit[i1](0, x[index]),
                    ),
                ),
            ),
            repeat(
                operands_2qubit.len,
                lambda i2: repeat(
                    connectivity_map.len,
                    lambda index: if_(
                        condition=is_parametrized[operands_1qubit.len + i2] == 1,
                        then=lambda: operands_2qubit[i2](
                            angle_params[
                                num_qubits
                                * sum(
                                    is_parametrized[
                                        0 : operands_1qubit.len
                                    ]  # type:ignore[index]
                                )
                                + connectivity_map.len
                                * sum(
                                    is_parametrized[
                                        operands_1qubit.len : operands_1qubit.len + i2
                                    ]
                                )
                                + floor((angle_params.len / reps) * r)
                                + index
                            ],
                            x[connectivity_map[index][0]],
                            x[connectivity_map[index][1]],
                        ),
                        else_=lambda: operands_2qubit[i2](
                            0,
                            x[connectivity_map[index][0]],
                            x[connectivity_map[index][1]],
                        ),
                    ),
                ),
            ),
        ],
    )
