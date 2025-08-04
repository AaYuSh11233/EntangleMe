from collections.abc import Mapping, Sequence
from typing import Literal

import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.amplitude_loading import (
    AMPLITUDE_IO_NAME,
    TARGET_OUTPUT_NAME,
)
from classiq.interface.model.handle_binding import (
    ConcreteHandleBinding,
    HandleBinding,
)
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumAssignmentOperation,
)
from classiq.interface.model.quantum_statement import HandleMetadata
from classiq.interface.model.quantum_type import QuantumBit, QuantumNumeric, QuantumType

MULTI_VARS_UNSUPPORTED_ERROR = (
    "Amplitude Loading with more than one input variable is unsupported."
)

VAR_TYPE_ILLEGAL = "Amplitude Loading input variable should be a quantum numeric"


class AmplitudeLoadingOperation(QuantumAssignmentOperation):
    kind: Literal["AmplitudeLoadingOperation"]

    _result_type: QuantumType = pydantic.PrivateAttr(default_factory=QuantumBit)

    @property
    def wiring_inouts(
        self,
    ) -> Mapping[str, ConcreteHandleBinding]:
        inouts = {self.result_name(): self.result_var}
        if len(self.var_handles) == 1:
            inouts[AMPLITUDE_IO_NAME] = self.var_handles[0]
        return inouts

    @property
    def readable_inouts(self) -> Sequence[HandleMetadata]:
        inouts = [
            HandleMetadata(
                handle=self.result_var,
                readable_location="on the left-hand side of an in-place assignment",
            )
        ]
        if len(self.var_handles) == 1:
            inouts.append(
                HandleMetadata(
                    handle=self.var_handles[0],
                    readable_location="in an expression",
                )
            )
        return inouts

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return {}

    def initialize_var_types(
        self,
        var_types: dict[str, QuantumType],
        machine_precision: int,
    ) -> None:
        if len(var_types) != 1:
            raise ClassiqValueError(MULTI_VARS_UNSUPPORTED_ERROR)
        var_type = list(var_types.values())[0]
        if not isinstance(var_type, QuantumNumeric):
            raise ClassiqValueError(VAR_TYPE_ILLEGAL)
        super().initialize_var_types(var_types, machine_precision)

    @classmethod
    def result_name(cls) -> str:
        return TARGET_OUTPUT_NAME
