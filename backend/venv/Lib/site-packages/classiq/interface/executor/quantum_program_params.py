from typing import Union

from pydantic import BaseModel

from classiq.interface.generator.model.preferences.preferences import Preferences
from classiq.interface.generator.quantum_program import QuantumProgram

ExecutionParams = dict[str, Union[float, int, list[int], list[float]]]


class TranspilationParams(BaseModel):
    quantum_program: QuantumProgram
    preferences: Preferences


class ParameterAssignmentsParams(BaseModel):
    quantum_program: QuantumProgram
    parameters: ExecutionParams
