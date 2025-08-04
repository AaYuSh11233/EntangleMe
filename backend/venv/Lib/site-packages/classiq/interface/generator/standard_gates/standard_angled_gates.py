from typing import Union

import pydantic

from classiq.interface.generator.standard_gates.standard_gates import _StandardGate


class RXGate(_StandardGate, angles=["theta"]):  # type: ignore[misc]
    """
    Rotation by theta about the X axis
    """


class RYGate(_StandardGate, angles=["theta"]):  # type: ignore[misc]
    """
    Rotation by theta about the Y axis
    """


class RZGate(_StandardGate, angles=["phi"]):  # type: ignore[misc]
    """
    Rotation by phi about the Z axis
    """


class RGate(_StandardGate, angles=["theta", "phi"]):  # type: ignore[misc]
    """
    Rotation by theta about the cos(phi)X + sin(phi)Y axis
    """


class PhaseGate(_StandardGate, angles=["theta"]):  # type: ignore[misc]
    """
    Add relative phase of lambda
    """

    _name: str = "p"


SingleRotationGate = Union[RZGate, RYGate, RXGate, PhaseGate]


class _DoubleRotationGate(_StandardGate, angles=["theta"]):  # type: ignore[misc]
    """
    Base class for RXX, RYY, RZZ
    """

    _num_target_qubits: pydantic.PositiveInt = pydantic.PrivateAttr(default=2)


class RXXGate(_DoubleRotationGate):  # type: ignore[misc]
    """
    Rotation by theta about the XX axis
    """


class RYYGate(_DoubleRotationGate):  # type: ignore[misc]
    """
    Rotation by theta about the YY axis
    """


class RZZGate(_DoubleRotationGate):  # type: ignore[misc]
    """
    Rotation by theta about the ZZ axis
    """
