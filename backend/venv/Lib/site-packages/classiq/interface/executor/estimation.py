import pydantic

from classiq.interface.chemistry.operator import PauliOperators
from classiq.interface.executor.quantum_code import QuantumCode


class OperatorsEstimation(pydantic.BaseModel):
    """
    Estimate the expectation value of a list of Pauli operators on a quantum state given
    by a quantum program.
    """

    quantum_program: QuantumCode
    operators: PauliOperators
