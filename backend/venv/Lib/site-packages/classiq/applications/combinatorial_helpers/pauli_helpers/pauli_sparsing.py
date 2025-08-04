from typing import Any, Union

import numpy as np


class SparsePauliOp:
    def __init__(self, paulis: Any, coeffs: Any) -> None:
        assert len(paulis) == len(
            coeffs
        ), "Paulis and coefficients lists must have the same length."
        self.paulis = np.array(paulis)
        self.coeffs = np.array(coeffs, dtype=complex)

    def __str__(self) -> str:
        terms = [f"{coef}*{pauli}" for coef, pauli in zip(self.coeffs, self.paulis)]
        return " + ".join(terms)

    def __add__(self, other: "SparsePauliOp") -> "SparsePauliOp":
        """Add two SparsePauliOp objects."""
        if not isinstance(other, SparsePauliOp):
            raise ValueError("Can only add SparsePauliOp objects.")
        new_paulis = np.concatenate([self.paulis, other.paulis])
        new_coeffs = np.concatenate([self.coeffs, other.coeffs])
        return SparsePauliOp(new_paulis, new_coeffs)

    def __mul__(self, other: Union[int, float, complex]) -> "SparsePauliOp":
        """Scalar multiplication of a SparsePauliOp."""
        if not isinstance(other, (int, float, complex)):
            raise ValueError("Can only multiply by scalar values.")
        new_coeffs = self.coeffs * other
        return SparsePauliOp(self.paulis, new_coeffs)
