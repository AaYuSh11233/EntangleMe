from typing import Literal

from classiq.qmod.builtins.structs import (
    QSVMFeatureMapPauli,
)
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CInt
from classiq.qmod.qmod_variable import QArray, QBit


@qfunc(external=True)
def pauli_feature_map(
    feature_map: QSVMFeatureMapPauli,
    qbv: QArray[QBit, Literal["get_field(feature_map, 'feature_dimension')"]],
) -> None:
    pass


@qfunc(external=True)
def bloch_sphere_feature_map(
    feature_dimension: CInt,
    qbv: QArray[QBit, Literal["ceiling(feature_dimension / 2)"]],
) -> None:
    pass
