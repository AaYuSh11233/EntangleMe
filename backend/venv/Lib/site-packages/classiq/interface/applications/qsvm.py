from collections.abc import Iterable as IterableType, Sequence
from typing import (
    Any,
    Optional,
    Union,
)

import numpy as np
import pydantic
from numpy.typing import ArrayLike
from pydantic import ConfigDict, field_validator

from classiq.interface.helpers.versioned_model import VersionedModel

DataList = list[list[float]]
LabelsInt = list[int]


def listify(obj: Union[IterableType, ArrayLike]) -> list:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, Sequence) and obj and isinstance(obj[0], np.ndarray):
        return np.array(obj).tolist()
    elif isinstance(obj, list):
        return obj
    else:
        return list(obj)  # type: ignore[arg-type]


def validate_array_to_list(name: str) -> Any:
    @field_validator(name, mode="before")
    def _listify(cls: type[pydantic.BaseModel], value: Any) -> Any:
        return listify(value)

    return _listify


Shape = tuple[int, ...]


class QSVMInternalState(VersionedModel):
    underscore_sparse: bool
    class_weight: list
    classes: list
    underscore_gamma: float
    underscore_base_fit: list
    support: list
    support_vectors: list
    underscore_n_support: list
    dual_coef_2: list
    intercept: list
    underscore_p_a: list
    underscore_p_b: list
    fit_status: int
    shape_fit: Shape
    underscore_intercept: list
    dual_coef: list

    class_weight__shape: Shape
    classes__shape: Shape
    underscore_base_fit__shape: Shape
    support__shape: Shape
    support_vectors__shape: Shape
    underscore_n_support__shape: Shape
    dual_coef_2__shape: Shape
    intercept__shape: Shape
    underscore_p_a__shape: Shape
    underscore_p_b__shape: Shape
    underscore_intercept__shape: Shape
    dual_coef__shape: Shape

    set_class_weight = validate_array_to_list("class_weight")
    set_classes = validate_array_to_list("classes")
    set_underscore_base_fit = validate_array_to_list("underscore_base_fit")
    set_support = validate_array_to_list("support")
    set_support_vectors = validate_array_to_list("support_vectors")
    set_underscore_n_support = validate_array_to_list("underscore_n_support")
    set_dual_coef_2 = validate_array_to_list("dual_coef_2")
    set_intercept = validate_array_to_list("intercept")
    set_underscore_p_a = validate_array_to_list("underscore_p_a")
    set_underscore_p_b = validate_array_to_list("underscore_p_b")
    set_underscore_intercept = validate_array_to_list("underscore_intercept")
    set_dual_coef = validate_array_to_list("dual_coef")


class QSVMData(VersionedModel):
    data: DataList
    labels: Optional[LabelsInt] = None
    internal_state: Optional[QSVMInternalState] = None
    model_config = ConfigDict(extra="forbid")

    @pydantic.field_validator("data", mode="before")
    @classmethod
    def set_data(cls, data: Union[IterableType, ArrayLike]) -> list:
        return listify(data)

    @pydantic.field_validator("labels", mode="before")
    @classmethod
    def set_labels(
        cls, labels: Optional[Union[IterableType, ArrayLike]]
    ) -> Optional[list]:
        if labels is None:
            return None
        else:
            return listify(labels)


class QSVMTestResult(VersionedModel):
    data: float  # between 0 to 1


class QSVMPredictResult(VersionedModel):
    data: list  # serialized np.array


Data = Union[DataList, np.ndarray]
Labels = Union[list[Any], np.ndarray]
