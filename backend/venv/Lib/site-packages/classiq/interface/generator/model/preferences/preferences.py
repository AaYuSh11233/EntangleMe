from collections.abc import Sequence
from enum import IntEnum
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union

import pydantic
from pydantic import Field
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Self, TypeAlias

from classiq.interface.backend.backend_preferences import (
    BackendPreferences,
)
from classiq.interface.backend.quantum_backend_providers import (
    AllBackendsNameByVendor,
    ProviderVendor,
)
from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.machine_precision import (
    DEFAULT_MACHINE_PRECISION,
)
from classiq.interface.generator.hardware.hardware_data import (
    BACKEND_VALIDATION_ERROR_MESSAGE,
    CustomHardwareSettings,
)
from classiq.interface.generator.model.preferences.randomness import create_random_seed
from classiq.interface.hardware import Provider
from classiq.interface.helpers.custom_pydantic_types import PydanticMachinePrecision

if TYPE_CHECKING:
    VisualizationLevel: TypeAlias = Optional[int]
else:
    VisualizationLevel: TypeAlias = Optional[Annotated[int, Field(ge=-1)]]

if TYPE_CHECKING:
    PydanticBackendName = str
else:
    PydanticBackendName = Annotated[
        str, Field(strict=True, pattern="^([.A-Za-z0-9_-][ .A-Za-z0-9_-]*)$")
    ]


class QuantumFormat(StrEnum):
    QASM = "qasm"
    QSHARP = "qsharp"
    QIR = "qir"
    IONQ = "ionq"
    CIRQ_JSON = "cirq_json"
    QASM_CIRQ_COMPATIBLE = "qasm_cirq_compatible"
    EXECUTION_SERIALIZATION = "_execution_serialization"


if TYPE_CHECKING:
    PydanticConstrainedQuantumFormatList = list[QuantumFormat]
else:
    PydanticConstrainedQuantumFormatList = Annotated[
        list[QuantumFormat], Field(min_length=1, max_length=len(QuantumFormat))
    ]


class OptimizationLevel(IntEnum):
    NONE = 0
    LIGHT = 1
    MEDIUM = 2
    HIGH = 3


class TranspilationOption(StrEnum):
    NONE = "none"
    DECOMPOSE = "decompose"
    AUTO_OPTIMIZE = "auto optimize"
    LIGHT = "light"
    MEDIUM = "medium"
    INTENSIVE = "intensive"
    CUSTOM = "custom"

    def __bool__(self) -> bool:
        return self != TranspilationOption.NONE


class Preferences(pydantic.BaseModel, extra="forbid"):
    """
    Preferences for synthesizing a quantum circuit.

    Attributes:
        machine_precision (int): Specifies the precision used for quantum operations.
            Defaults to `DEFAULT_MACHINE_PRECISION`.
        backend_service_provider (str): The provider company or cloud service for the
            requested backend. Defaults to `None`.
        backend_name (str): The name of the requested backend or target. Defaults to `None`.
        custom_hardware_settings (CustomHardwareSettings): Defines custom hardware
            settings for optimization. This field is ignored if backend preferences are
            specified.
        debug_mode (bool): If `True`, debug information is added to the
            synthesized result, potentially slowing down the synthesis. Useful for
            executing interactive algorithms. Defaults to `True`.
        optimization_level (OptimizationLevel) : The optimization level used during synthesis (0-3);
        determines the trade-off between synthesis speed and the quality of the results. Defaults to 3.
             OptimizationLevel Options:
                - NONE = 0
                - LIGHT = 1
                - MEDIUM = 2
                - HIGH = 3
        output_format (List[QuantumFormat]): Lists the output format(s)
            for the quantum circuit. Defaults to `[QuantumFormat.QASM]`.
            `QuantumFormat` Options:
                - QASM = "qasm"
                - QSHARP = "qsharp"
                - QIR = "qir"
                - IONQ = "ionq"
                - CIRQ_JSON = "cirq_json"
                - QASM_CIRQ_COMPATIBLE = "qasm_cirq_compatible"
        pretty_qasm (bool): If `True`, formats OpenQASM 2 outputs with line breaks
            inside gate declarations, improving readability. Defaults to `True`.
        qasm3 (Optional[bool]): If `True`, outputs OpenQASM 3.0 in addition to 2.0,
            applicable to relevant attributes in `GeneratedCircuit`. Defaults to `None`.
        transpilation_option (TranspilationOption): Sets the transpilation option to
            optimize the circuit. Defaults to `AUTO_OPTIMIZE`. See `TranspilationOption`
        solovay_kitaev_max_iterations (Optional[int]): Specifies the
            maximum number of iterations for the Solovay-Kitaev algorithm, if used.
            Defaults to `None`.
        timeout_seconds (int): Timeout setting for circuit synthesis
            in seconds. Defaults to `300`.
        optimization_timeout_seconds (Optional[int]): Specifies the
            timeout for optimization in seconds, or `None` for no optimization timeout.
            This will still adhere to the overall synthesis timeout. Defaults to `None`.
        random_seed (int): Random seed for circuit synthesis.

    Raises:
        ClassiqValueError:
            - If the optimization timeout is greater than or equal to the synthesis timeout.
            - If the `output_format` contains duplicate entries.
            - If `backend_name` is provided without `backend_service_provider` or vice versa.
        ValueError:
            - If `backend_service_provider` is not valid.
    """

    _backend_preferences: Optional[BackendPreferences] = pydantic.PrivateAttr(
        default=None
    )
    machine_precision: PydanticMachinePrecision = DEFAULT_MACHINE_PRECISION

    backend_service_provider: Optional[Union[Provider, ProviderVendor, str]] = (
        pydantic.Field(
            default=None,
            description="Provider company or cloud for the requested backend.",
        )
    )
    backend_name: Optional[Union[PydanticBackendName, AllBackendsNameByVendor]] = (
        pydantic.Field(
            default=None, description="Name of the requested backend or target."
        )
    )
    custom_hardware_settings: CustomHardwareSettings = pydantic.Field(
        default_factory=CustomHardwareSettings,
        description="Custom hardware settings which will be used during optimization. "
        "This field is ignored if backend preferences are given.",
    )
    debug_mode: bool = pydantic.Field(
        default=True,
        description="Add debug information to the synthesized result. "
        "Setting this option to False can potentially speed up the synthesis, and is "
        "recommended for executing iterative algorithms.",
    )
    synthesize_all_separately: bool = pydantic.Field(
        default=False,
        description="If true, a heuristic is used to determine if a function should be synthesized separately",
        deprecated=True,
    )
    optimization_level: OptimizationLevel = pydantic.Field(
        default=OptimizationLevel.LIGHT,
        description="The optimization level used during synthesis; determines the trade-off between synthesis speed and the quality of the results",
    )
    output_format: PydanticConstrainedQuantumFormatList = pydantic.Field(
        default=[QuantumFormat.QASM],
        description="The quantum circuit output format(s). ",
    )

    pretty_qasm: bool = pydantic.Field(
        True,
        description="Prettify the OpenQASM2 outputs (use line breaks inside the gate "
        "declarations).",
    )

    qasm3: Optional[bool] = pydantic.Field(
        None,
        description="Output OpenQASM 3.0 instead of OpenQASM 2.0. Relevant only for "
        "the `qasm` and `transpiled_circuit.qasm` attributes of `GeneratedCircuit`.",
    )

    transpilation_option: TranspilationOption = pydantic.Field(
        default=TranspilationOption.AUTO_OPTIMIZE,
        description="If true, the returned result will contain a "
        "transpiled circuit and its depth",
    )

    solovay_kitaev_max_iterations: Optional[pydantic.PositiveInt] = pydantic.Field(
        None,
        description="Maximum iterations for the Solovay-Kitaev algorithm (if applied).",
    )

    timeout_seconds: pydantic.PositiveInt = pydantic.Field(
        default=300, description="Generation timeout in seconds"
    )

    optimization_timeout_seconds: Optional[pydantic.PositiveInt] = pydantic.Field(
        default=None,
        description="Optimization timeout in seconds, or None for no "
        "optimization timeout (will still timeout when the generation timeout is over)",
    )
    random_seed: int = pydantic.Field(
        default_factory=create_random_seed,
        description="The random seed used for the generation",
    )

    @pydantic.field_validator("optimization_timeout_seconds", mode="before")
    @classmethod
    def optimization_timeout_less_than_generation_timeout(
        cls,
        optimization_timeout_seconds: Optional[pydantic.PositiveInt],
        info: ValidationInfo,
    ) -> Optional[pydantic.PositiveInt]:
        generation_timeout_seconds = info.data.get("timeout_seconds")
        if generation_timeout_seconds is None or optimization_timeout_seconds is None:
            return optimization_timeout_seconds
        if optimization_timeout_seconds >= generation_timeout_seconds:
            raise ClassiqValueError(
                f"Generation timeout ({generation_timeout_seconds})"
                f"is greater than or equal to "
                f"optimization timeout ({optimization_timeout_seconds}) "
            )
        return optimization_timeout_seconds

    @pydantic.field_validator("output_format", mode="before")
    @classmethod
    def make_output_format_list(cls, output_format: Any) -> list:
        if not isinstance(output_format, Sequence) or isinstance(output_format, str):
            output_format = [output_format]

        return output_format

    @pydantic.field_validator("output_format", mode="before")
    @classmethod
    def validate_output_format(
        cls,
        output_format: PydanticConstrainedQuantumFormatList,
        info: ValidationInfo,
    ) -> PydanticConstrainedQuantumFormatList:
        if len(output_format) != len(set(output_format)):
            raise ClassiqValueError(
                f"output_format={output_format}\n"
                "has at least one format that appears twice or more"
            )

        return output_format

    @pydantic.field_validator("backend_name")
    @classmethod
    def validate_backend_name(cls, backend_name: Optional[str]) -> Optional[str]:
        if backend_name is None:
            return backend_name
        return backend_name.rstrip()

    @pydantic.model_validator(mode="after")
    def validate_backend(self) -> Self:
        backend_name = self.backend_name
        backend_service_provider = self.backend_service_provider
        if (backend_name is None) != (backend_service_provider is None):
            raise ClassiqValueError(BACKEND_VALIDATION_ERROR_MESSAGE)
        return self

    @property
    def backend_preferences(self) -> Optional[BackendPreferences]:
        """
        Returns the backend preferences. If the backend preferences are not provided, the function sets the backend preferences according to backend name and provider.

        """
        if self.backend_name is None or self.backend_service_provider is None:
            return None
        if self._backend_preferences is None:
            self._backend_preferences = BackendPreferences(
                backend_name=self.backend_name,
                backend_service_provider=self.backend_service_provider,
            )
        return self._backend_preferences
