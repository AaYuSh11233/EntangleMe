from typing import Literal, Optional, Union

import numpy as np
import pydantic
from pydantic import ConfigDict

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqQSVMError, ClassiqValueError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import (
    DEFAULT_INPUT_NAME,
    DEFAULT_OUTPUT_NAME,
    FunctionParams,
)
from classiq.interface.helpers.hashable_pydantic_base_model import (
    HashablePydanticBaseModel,
)

VALID_PAULI_LETTERS = ("I", "X", "Y", "Z")


class QSVMFeatureMapEntanglement(StrEnum):
    FULL = "full"
    LINEAR = "linear"
    CIRCULAR = "circular"
    SCA = "sca"
    PAIRWISE = "pairwise"


class QSVMFeatureMapDimensional(HashablePydanticBaseModel):
    feature_dimension: Optional[int] = None
    model_config = ConfigDict(frozen=True)


class QSVMFeatureMapPauli(QSVMFeatureMapDimensional):
    map_type: Literal["pauli_feature_map"] = pydantic.Field(default="pauli_feature_map")
    reps: int = 2
    entanglement: QSVMFeatureMapEntanglement = QSVMFeatureMapEntanglement.LINEAR
    alpha: float = 2.0
    paulis: list[str] = ["Z", "ZZ"]
    parameter_prefix: str = "x"
    name: str = "PauliFeatureMap"

    @pydantic.field_validator("paulis", mode="before")
    @classmethod
    def set_paulis(cls, paulis: list[str]) -> list[str]:
        # iterate every letter in every string in the list of paulis
        for s in paulis:
            if not all(map(VALID_PAULI_LETTERS.__contains__, s.upper())):
                raise ClassiqValueError(
                    f"Invalid pauli string given: {s!r}. Expecting a combination of {VALID_PAULI_LETTERS}"
                )
        return list(map(str.upper, paulis))


class QSVMFeatureMapBlochSphere(QSVMFeatureMapDimensional):
    map_type: Literal["bloch_sphere_feature_map"] = pydantic.Field(
        default="bloch_sphere_feature_map"
    )


FeatureMapType = Union[QSVMFeatureMapBlochSphere, QSVMFeatureMapPauli]


class QSVMFeatureMap(FunctionParams):
    """
    Feature map circuit used for QSVM
    """

    feature_map: FeatureMapType = pydantic.Field(
        description="The feature map for the qsvm",
        discriminator="map_type",
    )

    @property
    def num_qubits(self) -> int:
        if not self.feature_map.feature_dimension:
            raise ClassiqQSVMError(
                "Feature dimension should be provided to create a circuit."
            )
        if isinstance(self.feature_map, QSVMFeatureMapPauli):
            return self.feature_map.feature_dimension
        else:
            return int(np.ceil(self.feature_map.feature_dimension / 2))

    def _create_ios(self) -> None:
        self._inputs = {
            DEFAULT_INPUT_NAME: RegisterUserInput(
                name=DEFAULT_INPUT_NAME, size=self.num_qubits
            )
        }
        self._outputs = {
            DEFAULT_OUTPUT_NAME: RegisterUserInput(
                name=DEFAULT_OUTPUT_NAME, size=self.num_qubits
            )
        }
