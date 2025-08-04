from dataclasses import dataclass
from typing import Optional, Union

from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.quantum_type import (
    QuantumNumeric,
    QuantumScalar,
    register_info_to_quantum_type,
)


@dataclass
class NumericAttributes:
    size: int
    is_signed: bool
    fraction_digits: int
    bounds: tuple[float, float]

    def __init__(
        self,
        size: int,
        is_signed: bool,
        fraction_digits: int,
        bounds: Optional[tuple[float, float]] = None,
        trim_bounds: bool = False,
    ) -> None:
        self.size = size
        self.is_signed = is_signed
        self.fraction_digits = fraction_digits
        if bounds is None:
            bounds = RegisterArithmeticInfo.get_maximal_bounds(
                size=size,
                is_signed=is_signed,
                fraction_places=fraction_digits,
            )
        if trim_bounds:
            bounds = (
                number_utils.limit_fraction_places(bounds[0], fraction_digits),
                number_utils.limit_fraction_places(bounds[1], fraction_digits),
            )
        self.bounds = bounds

    @property
    def lb(self) -> float:
        return self.bounds[0]

    @property
    def ub(self) -> float:
        return self.bounds[1]

    @property
    def integer_digits(self) -> int:
        return self.size - self.fraction_digits

    def to_quantum_numeric(self) -> QuantumNumeric:
        quantum_numeric = QuantumNumeric(
            size=Expression(expr=str(self.size)),
            is_signed=Expression(expr=str(self.is_signed)),
            fraction_digits=Expression(expr=str(self.fraction_digits)),
        )
        quantum_numeric.set_bounds(self.bounds)
        return quantum_numeric

    def to_register(self) -> RegisterArithmeticInfo:
        return RegisterArithmeticInfo(
            size=self.size,
            is_signed=self.is_signed,
            fraction_places=self.fraction_digits,
            bounds=self.bounds,
        )

    def trim_fraction_digits(self, machine_precision: int) -> "NumericAttributes":
        trimmed_digits = self.fraction_digits - machine_precision
        if trimmed_digits < 0:
            return self

        return NumericAttributes(
            size=self.size - trimmed_digits,
            is_signed=self.is_signed,
            fraction_digits=self.fraction_digits - trimmed_digits,
            bounds=self.bounds,
            trim_bounds=True,
        )

    @classmethod
    def from_bounds(
        cls,
        lb: float,
        ub: float,
        fraction_places: int,
        machine_precision: int,
        trim_bounds: bool = False,
    ) -> "NumericAttributes":
        size, is_signed, fraction_digits = number_utils.bounds_to_attributes(
            lb, ub, fraction_places, machine_precision
        )
        return cls(
            size=size,
            is_signed=is_signed,
            fraction_digits=fraction_digits,
            bounds=(lb, ub),
            trim_bounds=trim_bounds,
        )

    @classmethod
    def from_constant(
        cls,
        value: float,
        machine_precision: Optional[int] = None,
    ) -> "NumericAttributes":
        if machine_precision is not None:
            value = number_utils.limit_fraction_places(value, machine_precision)

        return cls(
            size=number_utils.size(value),
            is_signed=value < 0,
            fraction_digits=number_utils.fraction_places(value),
            bounds=(value, value),
        )

    @classmethod
    def from_quantum_scalar(
        cls,
        quantum_type: QuantumScalar,
        machine_precision: Optional[int] = None,
    ) -> "NumericAttributes":
        return cls(
            size=quantum_type.size_in_bits,
            is_signed=quantum_type.sign_value,
            fraction_digits=quantum_type.fraction_digits_value,
            bounds=quantum_type.get_effective_bounds(machine_precision),
        )

    @classmethod
    def from_register_arithmetic_info(
        cls,
        register: RegisterArithmeticInfo,
        machine_precision: Optional[int] = None,
    ) -> "NumericAttributes":
        return cls.from_quantum_scalar(
            quantum_type=register_info_to_quantum_type(register),
            machine_precision=machine_precision,
        )

    @classmethod
    def from_type_or_constant(
        cls,
        from_: Union[float, QuantumScalar, RegisterArithmeticInfo],
        machine_precision: Optional[int] = None,
    ) -> "NumericAttributes":
        if isinstance(from_, QuantumScalar):
            return cls.from_quantum_scalar(from_, machine_precision)
        if isinstance(from_, RegisterArithmeticInfo):
            return cls.from_register_arithmetic_info(from_, machine_precision)
        return cls.from_constant(from_, machine_precision)
