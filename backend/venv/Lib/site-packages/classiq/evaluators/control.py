from typing import Any

from sympy import Equality
from sympy.core.numbers import Number

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.arith.argument_utils import (
    unsigned_integer_interpretation,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.expressions.proxies.quantum.qmod_qscalar_proxy import (
    QmodQNumProxy,
    QmodQScalarProxy,
    QmodSizedProxy,
)

CONTROL_INOUT_NAME = "ctrl"


def type_name(obj: Any) -> str:
    if isinstance(obj, QmodSizedProxy):
        return obj.type_name
    return type(obj).__name__


def resolve_num_condition(condition: Equality) -> tuple[QmodSizedProxy, str]:
    ctrl, ctrl_val = condition.args
    if isinstance(ctrl, Number) and isinstance(ctrl_val, QmodQScalarProxy):
        ctrl, ctrl_val = ctrl_val, ctrl
    if not isinstance(ctrl, QmodSizedProxy) or not (isinstance(ctrl_val, Number)):
        _raise_numeric_condition_error(ctrl, ctrl_val)
    return ctrl, _calculate_ctrl_state(ctrl, float(ctrl_val))


def _calculate_ctrl_state(ctrl: QmodSizedProxy, ctrl_val: float) -> str:
    is_signed, fraction_places = _get_numeric_attributes(ctrl)

    reg = RegisterArithmeticInfo(
        size=ctrl.size, is_signed=is_signed, fraction_places=fraction_places
    )
    uint_ctrl_val = unsigned_integer_interpretation(ctrl_val, reg)

    _validate_control_value_sign(ctrl, ctrl_val, is_signed)
    _validate_control_var_qubits(ctrl, uint_ctrl_val, fraction_places, ctrl_val)

    return _to_twos_complement(uint_ctrl_val, ctrl.size)


def _get_numeric_attributes(ctrl: QmodSizedProxy) -> tuple[bool, int]:
    return (
        (ctrl.is_signed, ctrl.fraction_digits)
        if isinstance(ctrl, QmodQNumProxy)
        else (False, 0)
    )


def _validate_control_value_sign(
    ctrl: QmodSizedProxy, ctrl_val: float, is_signed: bool
) -> None:
    if not is_signed and ctrl_val < 0:
        raise ClassiqExpansionError(
            f"Variable {str(ctrl)!r} is not signed but control value "
            f"{ctrl_val} is negative"
        )


def _validate_control_var_qubits(
    ctrl: QmodSizedProxy,
    ctrl_val: int,
    fraction_places: int,
    orig_ctrl_val: float,
) -> None:
    required_qubits = _min_unsigned_bit_length(ctrl_val)
    fraction_places_message = (
        f" with {fraction_places} fraction digits" if fraction_places else ""
    )
    if ctrl.size < required_qubits:
        raise ClassiqExpansionError(
            f"Variable {str(ctrl)!r} has {ctrl.size} qubits{fraction_places_message} but control value "
            f"{str(orig_ctrl_val if fraction_places else int(orig_ctrl_val))!r} requires at least {required_qubits} qubits{fraction_places_message}"
        )


def _raise_numeric_condition_error(ctrl: Any, ctrl_val: Any) -> None:
    message = (
        "Control condition must be of the form '<quantum-variable> == "
        "<classical-number-expression>' or vice versa. "
    )
    prefix = f"Neither {ctrl!r} (type {type_name(ctrl)}) or {ctrl_val!r} (type {type_name(ctrl_val)}) is a "
    if not isinstance(ctrl, QmodSizedProxy) and not isinstance(
        ctrl_val, QmodSizedProxy
    ):
        message += prefix + "quantum variable."
    elif not isinstance(ctrl, Number) and not isinstance(ctrl_val, Number):
        message += prefix + "classical number."
    raise ClassiqExpansionError(message)


def _min_unsigned_bit_length(number: int) -> int:
    if number < 0:
        raise ClassiqExpansionError(
            f"Quantum register is not signed but control value "
            f"'{number}' is negative"
        )
    try:
        return 1 if number == 0 else number.bit_length()
    except AttributeError as e:
        raise e


def _to_twos_complement(value: int, bits: int) -> str:
    if value >= 0:
        return bin(value)[2:].zfill(bits)[::-1]
    return _to_negative_twos_complement(value, bits)


def _to_negative_twos_complement(value: int, bits: int) -> str:
    mask = (1 << bits) - 1
    value = (abs(value) ^ mask) + 1
    return bin(value)[:1:-1].rjust(bits, "1")
