from typing_extensions import TypeAlias

from classiq.interface.enum_utils import StrEnum
from classiq.interface.executor.quantum_instruction_set import QuantumInstructionSet
from classiq.interface.generator.model.preferences.preferences import QuantumFormat

Code: TypeAlias = str
CodeAndSyntax: TypeAlias = tuple[Code, QuantumInstructionSet]

INSTRUCTION_SET_TO_FORMAT: dict[QuantumInstructionSet, QuantumFormat] = {
    QuantumInstructionSet.QASM: QuantumFormat.QASM,
    QuantumInstructionSet.QSHARP: QuantumFormat.QSHARP,
    QuantumInstructionSet.IONQ: QuantumFormat.IONQ,
    QuantumInstructionSet.INTERNAL: QuantumFormat.EXECUTION_SERIALIZATION,
}
_MAXIMUM_STRING_LENGTH = 250


class QasmVersion(StrEnum):
    V2 = "2.0"
    V3 = "3.0"


class LongStr(str):
    def __repr__(self) -> str:
        if len(self) > _MAXIMUM_STRING_LENGTH:
            length = len(self)
            return f'"{self[:4]}...{self[-4:]}" (length={length})'
        return super().__repr__()
