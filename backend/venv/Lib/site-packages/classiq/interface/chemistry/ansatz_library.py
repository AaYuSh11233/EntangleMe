from typing import Optional

from pydantic import BaseModel


class HardwareEfficientConstraints(BaseModel):
    num_qubits: int
    num_two_qubit_gates: Optional[int] = None
    num_one_qubit_gates: Optional[int] = None
    max_depth: Optional[int] = None


class HardwareEfficient(BaseModel):
    structure: str
    constraints: HardwareEfficientConstraints
