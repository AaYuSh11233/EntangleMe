from typing import Any, Optional, cast

import pydantic

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.control_state import ControlState
from classiq.interface.generator.function_params import (
    FunctionParams,
    FunctionParamsNumericParameter,
)

CTRL = "CTRL"
TARGET = "TARGET"


class Mcu(FunctionParams):
    """
    Multi-controlled u-gate.
    Based on U(theta, phi, lam, gam) = e^(i*(gam + (phi + lam)/2)) * RZ(phi) * RY(theta) * RZ(lam)
    For a general gate U, four angles are required - theta, phi, lambda and gam.

    U(gam, phi,theta, lam) =
    e^(i*gam) *
    cos(theta/2) & -e^(i*lam)*sin(theta/2) \\
    e^(i*phi)*sin(theta/2) & e^(i*(phi+lam))*cos(theta/2) \\

    U(gam, phi,theta, lam) =
    e^(i*gam) *
    cos(theta/2)            &    -e^(i*lam)*sin(theta/2) \\
    e^(i*phi)*sin(theta/2)  &    e^(i*(phi+lam))*cos(theta/2) \\
    """

    theta: FunctionParamsNumericParameter = pydantic.Field(
        default=0, description="Theta radian angle."
    )
    phi: FunctionParamsNumericParameter = pydantic.Field(
        default=0, description="Phi radian angle."
    )
    lam: FunctionParamsNumericParameter = pydantic.Field(
        default=0, description="Lambda radian angle."
    )
    gam: FunctionParamsNumericParameter = pydantic.Field(
        default=0, description="gam radian angle."
    )

    num_ctrl_qubits: Optional[pydantic.PositiveInt] = pydantic.Field(
        default=None, description="The number of control qubits."
    )
    ctrl_state: Optional[str] = pydantic.Field(
        default=None, description="string of the control state"
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate_control(cls, values: Any) -> dict[str, Any]:
        num_ctrl_qubits = values.get("num_ctrl_qubits")
        ctrl_state = values.get("ctrl_state")

        if ctrl_state is not None:
            ctrl_state = cast(str, ctrl_state)
            ControlState.validate_control_string(ctrl_state)

        if ctrl_state is None and num_ctrl_qubits is None:
            raise ClassiqValueError("num_ctrl_qubits or ctrl_state must exist.")

        if ctrl_state is None and num_ctrl_qubits is not None:
            values["ctrl_state"] = "1" * num_ctrl_qubits
            ctrl_state = values["ctrl_state"]

        if num_ctrl_qubits is None and ctrl_state is not None:
            num_ctrl_qubits = len(ctrl_state)
            values["num_ctrl_qubits"] = num_ctrl_qubits

        if len(ctrl_state) != num_ctrl_qubits:
            raise ClassiqValueError(
                "control state length should be equal to the number of control qubits"
            )

        return values

    def _create_ios(self) -> None:
        if self.num_ctrl_qubits is None:
            raise ClassiqValueError("num_ctrl_qubits must have a valid value.")
        ctrl_register = RegisterUserInput(size=self.num_ctrl_qubits, name=CTRL)
        target_register = RegisterUserInput(size=1, name=TARGET)
        self._inputs = {reg.name: reg for reg in (ctrl_register, target_register)}
        self._outputs = {reg.name: reg for reg in (ctrl_register, target_register)}
