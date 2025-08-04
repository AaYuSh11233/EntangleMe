import dataclasses
from typing import Union

from classiq.interface.generator.excitations import EXCITATIONS_TYPE_EXACT
from classiq.interface.generator.ucc import default_excitation_factory


@dataclasses.dataclass
class UCCParameters:
    excitations: EXCITATIONS_TYPE_EXACT = dataclasses.field(
        default_factory=default_excitation_factory
    )


@dataclasses.dataclass
class HVAParameters:
    reps: int


@dataclasses.dataclass
class HEAParameters:
    reps: int
    num_qubits: int
    connectivity_map: list[tuple[int, int]]
    one_qubit_gates: list[str]
    two_qubit_gates: list[str]


AnsatzParameters = Union[UCCParameters, HVAParameters, HEAParameters]
