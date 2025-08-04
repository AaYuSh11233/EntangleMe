import pydantic

from classiq.interface.generator import function_params
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import FunctionParamsNumericParameter
from classiq.interface.generator.standard_gates.standard_gates import (
    DEFAULT_STANDARD_GATE_ARG_NAME,
)


class UGate(function_params.FunctionParams):
    """
    Matrix representation:

    U(gam, phi,theta, lam) =
    e^(i*gam) *
    cos(theta/2) & -e^(i*lam)*sin(theta/2) \\
    e^(i*phi)*sin(theta/2) & e^(i*(phi+lam))*cos(theta/2) \\
    """

    theta: FunctionParamsNumericParameter = pydantic.Field(
        description="Angle to rotate by the Y-axis.",
    )

    phi: FunctionParamsNumericParameter = pydantic.Field(
        description="First angle to rotate by the Z-axis.",
    )

    lam: FunctionParamsNumericParameter = pydantic.Field(
        description="Second angle to rotate by the Z-axis.",
    )

    gam: FunctionParamsNumericParameter = pydantic.Field(
        description="Angle to apply phase gate by.",
    )

    _inputs = pydantic.PrivateAttr(
        default={
            DEFAULT_STANDARD_GATE_ARG_NAME: RegisterUserInput(
                name=DEFAULT_STANDARD_GATE_ARG_NAME, size=1
            )
        }
    )
    _outputs = pydantic.PrivateAttr(
        default={
            DEFAULT_STANDARD_GATE_ARG_NAME: RegisterUserInput(
                name=DEFAULT_STANDARD_GATE_ARG_NAME, size=1
            )
        }
    )

    @property
    def is_parametric(self) -> bool:
        return not all(
            isinstance(getattr(self, angle), (float, int))
            for angle in ["theta", "phi", "lam", "gam"]
        )
