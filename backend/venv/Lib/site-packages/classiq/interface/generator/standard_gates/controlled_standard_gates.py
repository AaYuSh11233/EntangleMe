from typing import Literal, Optional, Union

import pydantic
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.control_state import ControlState
from classiq.interface.generator.standard_gates.standard_gates import (
    DEFAULT_STANDARD_GATE_ARG_NAME,
    _StandardGate,
)

CONTROLLED_GATE_CONTROL: str = "CTRL"
CONTROLLED_GATE_TARGET: str = DEFAULT_STANDARD_GATE_ARG_NAME
DEFAULT_NUM_CTRL_QUBITS: int = 1

CtrlState = Optional[Union[pydantic.StrictStr, pydantic.NonNegativeInt]]


class ControlledGate(_StandardGate):  # type: ignore[misc]
    """
    Base model for controlled Gates
    """

    num_ctrl_qubits: pydantic.PositiveInt = pydantic.Field(
        default=DEFAULT_NUM_CTRL_QUBITS
    )
    ctrl_state: CtrlState = pydantic.Field(
        description="The control state in decimal or as a bit string (e.g. '1011'). If not specified, the control "
        "state is 2**num_ctrl_qubits - 1.\n"
        "The gate will be performed if the state of the control qubits matches the control state",
        default=None,
        validate_default=True,
    )

    @pydantic.field_validator("ctrl_state")
    @classmethod
    def _validate_ctrl_state(
        cls, ctrl_state: CtrlState, info: ValidationInfo
    ) -> CtrlState:
        num_ctrl_qubits: int = info.data.get("num_ctrl_qubits", DEFAULT_NUM_CTRL_QUBITS)
        ctrl_state = ctrl_state if ctrl_state is not None else "1" * num_ctrl_qubits

        if isinstance(ctrl_state, str) and len(ctrl_state) != num_ctrl_qubits:
            raise ClassiqValueError(
                f"Invalid control state: {ctrl_state!r}. "
                f"Expected {num_ctrl_qubits} qubits"
            )
        elif isinstance(ctrl_state, int) and ctrl_state >= 2**num_ctrl_qubits:
            raise ClassiqValueError(
                f"Invalid control state: {ctrl_state}. "
                f"Expected value between 0 and {2**num_ctrl_qubits-1}"
            )
        return ctrl_state

    def to_control_state(self) -> ControlState:
        ctrl_state_str = (
            _num_to_control_string(self.ctrl_state, self.num_ctrl_qubits)
            if isinstance(self.ctrl_state, int)
            else self.ctrl_state
        )
        return ControlState(name=CONTROLLED_GATE_CONTROL, ctrl_state=ctrl_state_str)

    def _create_ios(self) -> None:
        _StandardGate._create_ios(self)
        control = RegisterUserInput(
            name=CONTROLLED_GATE_CONTROL, size=self.num_ctrl_qubits
        )
        self._inputs[CONTROLLED_GATE_CONTROL] = control
        self._outputs[CONTROLLED_GATE_CONTROL] = control


def _num_to_control_string(ctrl_state_int: int, num_ctrl_qubits: int) -> str:
    return format(ctrl_state_int, f"0{num_ctrl_qubits}b")


class CXGate(ControlledGate):  # type: ignore[misc]
    """
    The Controlled-X Gate
    """

    num_ctrl_qubits: Literal[1] = pydantic.Field(default=1)

    def get_power_order(self) -> int:
        return 2


class CCXGate(ControlledGate):  # type: ignore[misc]
    """
    The Double Controlled-X Gate
    """

    num_ctrl_qubits: Literal[2] = pydantic.Field(default=2)

    def get_power_order(self) -> int:
        return 2


class C3XGate(ControlledGate):  # type: ignore[misc]
    """
    The X Gate controlled on 3 qubits
    """

    _name: str = "mcx"
    num_ctrl_qubits: Literal[3] = pydantic.Field(default=3)

    def get_power_order(self) -> int:
        return 2


class C4XGate(ControlledGate):  # type: ignore[misc]
    """
    The X Gate controlled on 4 qubits
    """

    _name: str = "mcx"
    num_ctrl_qubits: Literal[4] = pydantic.Field(default=4)

    def get_power_order(self) -> int:
        return 2


class CYGate(ControlledGate):  # type: ignore[misc]
    """
    The Controlled-Y Gate
    """

    def get_power_order(self) -> int:
        return 2


class CZGate(ControlledGate):  # type: ignore[misc]
    """
    The Controlled-Z Gate
    """

    def get_power_order(self) -> int:
        return 2


class CHGate(ControlledGate):  # type: ignore[misc]
    """
    The Controlled-H Gate
    """

    def get_power_order(self) -> int:
        return 2


class CSXGate(ControlledGate):  # type: ignore[misc]
    """
    The Controlled-SX Gate
    """

    def get_power_order(self) -> int:
        return 4


class CRXGate(ControlledGate, angles=["theta"]):  # type: ignore[misc]
    """
    The Controlled-RX Gate
    """


class CRYGate(ControlledGate, angles=["theta"]):  # type: ignore[misc]
    """
    The Controlled-RY Gate
    """


class CRZGate(ControlledGate, angles=["theta"]):  # type: ignore[misc]
    """
    The Controlled-RZ Gate
    """


class CPhaseGate(ControlledGate, angles=["theta"]):  # type: ignore[misc]
    """
    The Controlled-Phase Gate
    """

    _name: str = "cp"


class MCPhaseGate(ControlledGate, angles=["lam"]):  # type: ignore[misc]
    """
    The Controlled-Phase Gate
    """

    _name: str = "mcphase"
