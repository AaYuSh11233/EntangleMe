from typing import Optional, cast

import numpy as np
from openfermion.ops.operators.qubit_operator import QubitOperator
from openfermion.utils.operator_utils import count_qubits

from classiq.interface.exceptions import ClassiqValueError

from classiq.qmod.builtins.enums import Pauli
from classiq.qmod.builtins.structs import IndexedPauli, SparsePauliOp, SparsePauliTerm


def _get_n_qubits(qubit_op: QubitOperator, n_qubits: Optional[int]) -> int:
    min_n_qubits = cast(int, count_qubits(qubit_op))
    if n_qubits is None:
        return min_n_qubits

    if n_qubits < min_n_qubits:
        raise ClassiqValueError(
            f"The operator acts on {min_n_qubits} and cannot be cast to a PauliTerm on {n_qubits}"
        )
    return n_qubits


def qubit_op_to_pauli_terms(
    qubit_op: QubitOperator, n_qubits: Optional[int] = None
) -> SparsePauliOp:
    n_qubits = _get_n_qubits(qubit_op, n_qubits)
    return SparsePauliOp(
        terms=[
            SparsePauliTerm(
                paulis=[  # type:ignore[arg-type]
                    IndexedPauli(
                        pauli=getattr(Pauli, pauli),
                        index=n_qubits - qubit - 1,
                    )
                    for qubit, pauli in term[::-1]
                ],
                coefficient=coeff,
            )
            for term, coeff in qubit_op.terms.items()
        ],
        num_qubits=n_qubits,
    )


_PAULIS_TO_XZ = {"I": (0, 0), "X": (1, 0), "Z": (0, 1), "Y": (1, 1)}
_XZ_TO_PAULIS = {(0, 0): "I", (1, 0): "X", (0, 1): "Z", (1, 1): "Y"}


def qubit_op_to_xz_matrix(
    qubit_op: QubitOperator, n_qubits: Optional[int] = None
) -> np.ndarray:
    n_qubits = _get_n_qubits(qubit_op, n_qubits)
    xz_mat = np.zeros((len(qubit_op.terms), 2 * n_qubits), dtype=np.int8)

    for row, (term, _) in zip(xz_mat, qubit_op.terms.items()):
        for qubit, pauli in term:
            row[qubit], row[n_qubits + qubit] = _PAULIS_TO_XZ[pauli]

    return xz_mat


def xz_matrix_to_qubit_op(xz_mat: np.ndarray) -> QubitOperator:
    if len(xz_mat.shape) == 1:
        xz_mat = np.array([xz_mat])

    qubit_op = QubitOperator()
    n_qubits = xz_mat.shape[1] // 2
    for row in xz_mat:
        op = tuple(
            (qubit, pauli)
            for qubit in range(n_qubits)
            if (pauli := _XZ_TO_PAULIS[(row[qubit], row[n_qubits + qubit])]) != "I"
        )
        if op:
            qubit_op += QubitOperator(op, 1)

    return qubit_op
