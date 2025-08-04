from __future__ import annotations

from pyomo.core.base.var import VarData

from classiq.interface.generator.function_params import IOName

from classiq.applications.combinatorial_helpers import encoding_utils
from classiq.applications.combinatorial_helpers.encoding_mapping import EncodingMapping

AUXILIARY_NAME = "auxiliary"


class InternalQuantumReg:
    def __init__(self, size: int, name: str) -> None:
        self.name = name
        self.size = size


class MemoryMapping:
    def __init__(
        self,
        variables: list[VarData],
        vars_encoding_mapping: EncodingMapping | None = None,
    ) -> None:
        self.substitution_dict: dict[int, InternalQuantumReg] = dict()
        self.qubit_allocation: dict[IOName, tuple[int, int]] = dict()
        self.vars_encoding_mapping: EncodingMapping | None = vars_encoding_mapping
        self.vars: list[VarData] = variables
        self._allocate_memory()

    def __len__(self) -> int:
        return len(self.substitution_dict)

    def _allocate_memory(self) -> None:
        for var_data in self.vars:
            if (
                not self.vars_encoding_mapping
                or encoding_utils.get_var_span(var_data) == 1
            ):
                num_qubits_var = 1
            else:
                num_qubits_var = len(
                    self.vars_encoding_mapping.get_encoding_vars(var_data)
                )

            self.substitution_dict[id(var_data)] = InternalQuantumReg(
                num_qubits_var, "q"
            )
            var_name = get_var_name(var_data)
            self.qubit_allocation[var_name] = (
                self._variable_qubits_allocated,
                num_qubits_var,
            )

    @property
    def qregs(self) -> list[InternalQuantumReg]:
        return list(self.substitution_dict.values())

    @property
    def _variable_qubits_allocated(self) -> int:
        return sum(
            num_qubits
            for name, (_, num_qubits) in self.qubit_allocation.items()
            if name != AUXILIARY_NAME
        )


def get_var_name(var: VarData) -> str:
    return (
        var.name.replace("[", "")
        .replace("]", "")
        .replace(",", "")
        .replace("'", "")
        .replace('"', "")
    )
