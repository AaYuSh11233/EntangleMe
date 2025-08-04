from typing import Annotated, Optional

import numpy
import pydantic
from pydantic import ConfigDict, Field, StringConstraints

from classiq.interface.backend.quantum_backend_providers import AnalyzerProviderVendor
from classiq.interface.chemistry.ground_state_problem import MoleculeProblem
from classiq.interface.executor.optimizer_preferences import OptimizerPreferences
from classiq.interface.generator.hardware.hardware_data import SynthesisHardwareData
from classiq.interface.generator.model.preferences.preferences import (
    TranspilationOption,
)
from classiq.interface.hardware import Provider
from classiq.interface.helpers.custom_pydantic_types import PydanticNonEmptyString

MAX_KB_OF_FILE = 50000
MAX_FILE_LENGTH = MAX_KB_OF_FILE * 1024

MAX_QUBITS = 100
MIN_QUBITS = 0
MAX_COUNTS = 1000
MAX_NUM_CLIFFORD = 1000
MAX_NAME_LENGTH = 100


class AnalysisParams(pydantic.BaseModel):
    qasm: PydanticNonEmptyString = Field(..., max_length=MAX_FILE_LENGTH)


class HardwareListParams(pydantic.BaseModel):
    devices: Optional[list[PydanticNonEmptyString]] = pydantic.Field(
        default=None, description="Devices"
    )
    providers: list[Provider]
    from_ide: bool = Field(default=False)

    @pydantic.field_validator("providers")
    @classmethod
    def set_default_providers(
        cls, providers: Optional[list[AnalyzerProviderVendor]]
    ) -> list[AnalyzerProviderVendor]:
        if providers is None:
            providers = list(AnalyzerProviderVendor)
        return providers


class AnalysisOptionalDevicesParams(HardwareListParams):
    qubit_count: int = pydantic.Field(
        default=...,
        description="number of qubits in the data",
        ge=MIN_QUBITS,
        le=MAX_QUBITS,
    )


class GateNamsMapping(pydantic.BaseModel):
    qasm_name: Annotated[
        str, Annotated[str, StringConstraints(max_length=MAX_NAME_LENGTH)]
    ]
    display_name: Annotated[
        str, Annotated[str, StringConstraints(max_length=MAX_NAME_LENGTH)]
    ]


class LatexParams(AnalysisParams):
    gate_names: list[GateNamsMapping] = pydantic.Field(
        default=..., description="List of gate names as apper in the qasm"
    )


class AnalysisHardwareTranspilationParams(pydantic.BaseModel):
    hardware_data: Optional[SynthesisHardwareData] = None
    random_seed: int
    transpilation_option: TranspilationOption


class AnalysisHardwareListParams(AnalysisParams, HardwareListParams):
    transpilation_params: AnalysisHardwareTranspilationParams


class HardwareParams(pydantic.BaseModel):
    device: PydanticNonEmptyString = pydantic.Field(default=None, description="Devices")
    provider: AnalyzerProviderVendor


class AnalysisHardwareParams(AnalysisParams, HardwareParams):
    pass


class CircuitAnalysisHardwareParams(AnalysisParams):
    provider: Provider
    device: PydanticNonEmptyString


class AnalysisRBParams(pydantic.BaseModel):
    hardware: str
    counts: list[
        dict[
            str, Annotated[int, Annotated[int, Field(strict=True, gt=0, le=MAX_COUNTS)]]
        ]
    ]
    num_clifford: list[
        Annotated[int, Annotated[int, Field(strict=True, gt=0, le=MAX_NUM_CLIFFORD)]]
    ]


class ChemistryGenerationParams(pydantic.BaseModel):
    model_config = ConfigDict(title="Chemistry")

    molecule: MoleculeProblem = pydantic.Field(
        title="Molecule",
        default=...,
        description="The molecule to generate the VQE ansatz for",
    )
    optimizer_preferences: OptimizerPreferences = pydantic.Field(
        default=..., description="Execution options for the classical Optimizer"
    )

    def initial_point(self) -> Optional[numpy.ndarray]:
        if self.optimizer_preferences.initial_point is not None:
            return numpy.ndarray(
                self.optimizer_preferences.initial_point  # type: ignore[arg-type]
            )
        else:
            return None
