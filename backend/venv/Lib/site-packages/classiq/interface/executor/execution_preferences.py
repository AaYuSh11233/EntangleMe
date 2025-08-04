from typing import Optional

import pydantic

from classiq.interface.backend.backend_preferences import (
    BackendPreferencesTypes,
    backend_preferences_field,
)
from classiq.interface.backend.quantum_backend_providers import (
    ClassiqSimulatorBackendNames,
)
from classiq.interface.enum_utils import ReprEnum
from classiq.interface.executor.optimizer_preferences import OptimizerType
from classiq.interface.generator.model.preferences.preferences import (
    TranspilationOption,
)
from classiq.interface.generator.model.preferences.randomness import create_random_seed
from classiq.interface.generator.noise_properties import NoiseProperties


class QaeWithQpeEstimationMethod(int, ReprEnum):
    MAXIMUM_LIKELIHOOD = 0
    BEST_FIT = 1


class ExecutionPreferences(pydantic.BaseModel):
    """
    Represents the execution settings for running a quantum program.
    Execution preferences for running a quantum program.

    For more details, refer to:
    ExecutionPreferences example: [ExecutionPreferences](https://docs.classiq.io/latest/user-guide/execution/#execution-preferences)..


    Attributes:
        noise_properties (Optional[NoiseProperties]): Properties defining the noise in the quantum circuit. Defaults to `None`.
        random_seed (int): The random seed used for the execution. Defaults to a randomly generated seed.
        backend_preferences (BackendPreferencesTypes): Preferences for the backend used to execute the circuit.
            Defaults to the Classiq Simulator.
        num_shots (Optional[pydantic.PositiveInt]): The number of shots (executions) to be performed.
        transpile_to_hardware (TranspilationOption): Option to transpile the circuit to the hardware's basis gates
            before execution. Defaults to `TranspilationOption.DECOMPOSE`.
        job_name (Optional[str]): The name of the job, with a minimum length of 1 character.
    """

    noise_properties: Optional[NoiseProperties] = pydantic.Field(
        default=None, description="Properties of the noise in the circuit"
    )
    random_seed: int = pydantic.Field(
        default_factory=create_random_seed,
        description="The random seed used for the execution",
    )
    backend_preferences: BackendPreferencesTypes = backend_preferences_field(
        backend_name=ClassiqSimulatorBackendNames.SIMULATOR
    )
    num_shots: Optional[pydantic.PositiveInt] = pydantic.Field(default=None)
    transpile_to_hardware: TranspilationOption = pydantic.Field(
        default=TranspilationOption.DECOMPOSE,
        description="Transpile the circuit to the hardware basis gates before execution",
        title="Transpilation Option",
    )
    job_name: Optional[str] = pydantic.Field(
        min_length=1, description="The job name", default=None
    )


__all__ = [
    "ExecutionPreferences",
    "NoiseProperties",
    "OptimizerType",
    "QaeWithQpeEstimationMethod",
]
