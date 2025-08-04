from classiq.interface.exceptions import ClassiqNonNumericCoefficientInPauliError
from classiq.interface.generator.functions.qmod_python_interface import QmodPyStruct
from classiq.interface.helpers.custom_pydantic_types import PydanticPauliList

from classiq.qmod.builtins.enums import Pauli
from classiq.qmod.builtins.structs import (
    IndexedPauli,
    PauliTerm,
    SparsePauliOp,
    SparsePauliTerm,
)


def pauli_operator_to_hamiltonian(pauli_list: PydanticPauliList) -> list[PauliTerm]:
    pauli_terms: list[PauliTerm] = []
    for pauli_term in pauli_list:
        if not isinstance(pauli_term[1], complex) or pauli_term[1].imag != 0:
            raise ClassiqNonNumericCoefficientInPauliError(
                "Coefficient is not a number."
            )
        term = PauliTerm(
            [Pauli[p] for p in pauli_term[0]],  # type: ignore[arg-type]
            pauli_term[1].real,  # type: ignore[arg-type]
        )
        pauli_terms.append(term)

    return pauli_terms


def pauli_operator_to_sparse_hamiltonian(
    pauli_list: list[PauliTerm],
) -> SparsePauliOp:
    pauli_terms: list[SparsePauliTerm] = []
    for pauli_term in pauli_list:
        term = SparsePauliTerm(
            paulis=[  # type:ignore[arg-type]
                IndexedPauli(pauli=p, index=i)  # type:ignore[arg-type]
                for i, p in enumerate(pauli_term.pauli[::-1])
            ],
            coefficient=pauli_term.coefficient,
        )
        pauli_terms.append(term)

    return SparsePauliOp(
        terms=pauli_terms,
        num_qubits=len(pauli_list[0].pauli),  # type: ignore[arg-type]
    )


def pauli_enum_to_str(pauli: Pauli) -> str:
    return {
        Pauli.I: "Pauli.I",
        Pauli.X: "Pauli.X",
        Pauli.Y: "Pauli.Y",
        Pauli.Z: "Pauli.Z",
    }[pauli]


def _pauli_terms_to_qmod(hamiltonian: list[PauliTerm]) -> str:
    qmod_strings = []
    for term in hamiltonian:
        pauli_str = ", ".join([pauli_enum_to_str(p) for p in term.pauli])  # type: ignore[attr-defined]
        qmod_strings.append(
            f"struct_literal(PauliTerm, pauli=[{pauli_str}], coefficient={term.coefficient})"
        )

    return ", ".join(qmod_strings)


def _pauli_dict_to_pauli_terms(hamiltonian: list[QmodPyStruct]) -> list[PauliTerm]:
    return [PauliTerm(**struct) for struct in hamiltonian]
