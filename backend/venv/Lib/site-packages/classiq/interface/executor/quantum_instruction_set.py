from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError


class QuantumInstructionSet(StrEnum):
    QASM = "qasm"
    QSHARP = "qsharp"
    IONQ = "ionq"
    INTERNAL = "_internal"

    @classmethod
    def from_suffix(cls, suffix: str) -> "QuantumInstructionSet":
        if suffix == "qasm":
            return QuantumInstructionSet.QASM
        if suffix == "qs":
            return QuantumInstructionSet.QSHARP
        if suffix == "ionq":
            return QuantumInstructionSet.IONQ
        raise ClassiqValueError("Illegal suffix")
