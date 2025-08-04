from typing import TYPE_CHECKING, Any, Literal, Optional

import pydantic
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self

from classiq.interface.ast_node import HashableASTNode
from classiq.interface.exceptions import (
    ClassiqInternalExpansionError,
    ClassiqValueError,
)
from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.arith.register_user_input import (
    RegisterArithmeticInfo,
    RegisterUserInput,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.quantum.qmod_qarray_proxy import (
    QmodQArrayProxy,
)
from classiq.interface.generator.expressions.proxies.quantum.qmod_qscalar_proxy import (
    QmodQBitProxy,
    QmodQNumProxy,
    QmodQScalarProxy,
)
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.helpers.custom_pydantic_types import PydanticFloatTuple
from classiq.interface.helpers.pydantic_model_helpers import values_with_discriminator
from classiq.interface.model.handle_binding import HandleBinding

if TYPE_CHECKING:
    from classiq.interface.generator.functions.concrete_types import ConcreteQuantumType


class QuantumType(HashableASTNode):
    model_config = ConfigDict(extra="forbid")

    _size_in_bits: Optional[int] = pydantic.PrivateAttr(default=None)

    def _update_size_in_bits_from_declaration(self) -> None:
        pass

    @property
    def size_in_bits(self) -> int:
        self._update_size_in_bits_from_declaration()
        if self._size_in_bits is None:
            raise ClassiqValueError("Trying to retrieve unknown size of quantum type")
        return self._size_in_bits

    @property
    def has_size_in_bits(self) -> bool:
        self._update_size_in_bits_from_declaration()
        return self._size_in_bits is not None

    def set_size_in_bits(self, val: int) -> None:
        self._size_in_bits = val

    @property
    def minimal_size_in_bits(self) -> int:
        raise NotImplementedError

    def get_proxy(self, handle: "HandleBinding") -> QmodSizedProxy:
        return QmodSizedProxy(handle=handle, size=self.size_in_bits)

    @property
    def qmod_type_name(self) -> str:
        raise NotImplementedError

    @property
    def raw_qmod_type_name(self) -> str:
        return self.qmod_type_name

    @property
    def type_name(self) -> str:
        raise NotImplementedError

    @property
    def is_instantiated(self) -> bool:
        raise NotImplementedError

    @property
    def is_evaluated(self) -> bool:
        raise NotImplementedError

    @property
    def expressions(self) -> list[Expression]:
        return []


class QuantumScalar(QuantumType):
    def get_proxy(self, handle: "HandleBinding") -> QmodQScalarProxy:
        return QmodQScalarProxy(handle, size=self.size_in_bits)

    @property
    def has_sign(self) -> bool:
        raise NotImplementedError

    @property
    def sign_value(self) -> bool:
        raise NotImplementedError

    @property
    def has_fraction_digits(self) -> bool:
        raise NotImplementedError

    @property
    def fraction_digits_value(self) -> int:
        raise NotImplementedError

    def get_effective_bounds(
        self, machine_precision: Optional[int] = None
    ) -> tuple[float, float]:
        raise NotImplementedError

    @property
    def is_qbit(self) -> bool:
        return (
            self.size_in_bits == 1
            and self.fraction_digits_value == 0
            and not self.sign_value
        )


class QuantumBit(QuantumScalar):
    kind: Literal["qbit"]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._size_in_bits = 1

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "qbit")

    @property
    def qmod_type_name(self) -> str:
        return "QBit"

    def get_proxy(self, handle: "HandleBinding") -> QmodQBitProxy:
        return QmodQBitProxy(handle)

    @property
    def type_name(self) -> str:
        return "Quantum bit"

    @property
    def is_instantiated(self) -> bool:
        return True

    @property
    def is_evaluated(self) -> bool:
        return True

    @property
    def has_sign(self) -> bool:
        return True

    @property
    def sign_value(self) -> bool:
        return False

    @property
    def has_fraction_digits(self) -> bool:
        return True

    @property
    def fraction_digits_value(self) -> int:
        return 0

    def get_effective_bounds(
        self, machine_precision: Optional[int] = None
    ) -> tuple[float, float]:
        return (0, 1)

    @property
    def minimal_size_in_bits(self) -> int:
        return 1


class QuantumBitvector(QuantumType):
    element_type: "ConcreteQuantumType" = Field(
        discriminator="kind", default_factory=QuantumBit
    )
    kind: Literal["qvec"]
    length: Optional[Expression] = Field(default=None)

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "qvec")

    def _update_size_in_bits_from_declaration(self) -> None:
        self.element_type._update_size_in_bits_from_declaration()
        if self.element_type.has_size_in_bits and self.has_constant_length:
            assert self.length is not None
            self._size_in_bits = (
                self.element_type.size_in_bits * self.length.to_int_value()
            )

    @property
    def has_length(self) -> bool:
        return self.length is not None and self.length.is_evaluated()

    @property
    def has_constant_length(self) -> bool:
        return (
            self.length is not None
            and self.length.is_evaluated()
            and self.length.is_constant()
        )

    @property
    def length_value(self) -> int:
        if not self.has_length:
            raise ClassiqValueError(
                "Tried to access unevaluated length of quantum array"
            )
        assert self.length is not None
        return self.length.to_int_value()

    def get_proxy(self, handle: "HandleBinding") -> QmodQArrayProxy:
        element_size = self.element_type.size_in_bits
        assert self.size_in_bits % element_size == 0
        return QmodQArrayProxy(
            handle,
            self.element_type,
            element_size,
            self.size_in_bits // element_size,
        )

    @property
    def qmod_type_name(self) -> str:
        element_type = [self.element_type.qmod_type_name]
        length = [self.length.expr] if self.length is not None else []
        return f"QArray[{', '.join(element_type + length)}]"

    @property
    def raw_qmod_type_name(self) -> str:
        return "QArray"

    @property
    def type_name(self) -> str:
        return "Quantum array"

    @property
    def is_instantiated(self) -> bool:
        return self.length is not None and self.element_type.is_instantiated

    @property
    def is_evaluated(self) -> bool:
        return (
            self.length is not None
            and self.length.is_evaluated()
            and self.element_type.is_evaluated
        )

    @property
    def expressions(self) -> list[Expression]:
        exprs = self.element_type.expressions
        if self.length is not None:
            exprs.append(self.length)
        return exprs

    @property
    def minimal_size_in_bits(self) -> int:
        if self.has_constant_length:
            length = self.length_value
        else:
            length = 1
        return length * self.element_type.minimal_size_in_bits


class QuantumNumeric(QuantumScalar):
    kind: Literal["qnum"]

    size: Optional[Expression] = pydantic.Field(default=None)
    is_signed: Optional[Expression] = pydantic.Field(default=None)
    fraction_digits: Optional[Expression] = pydantic.Field(default=None)

    _bounds: Optional[PydanticFloatTuple] = pydantic.PrivateAttr(default=None)

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "qnum")

    @pydantic.model_validator(mode="after")
    def _validate_fields(self) -> Self:
        has_sign = self.is_signed is not None
        has_fraction_digits = self.fraction_digits is not None
        if (has_sign and not has_fraction_digits) or (
            not has_sign and has_fraction_digits
        ):
            raise ClassiqValueError(
                "Assign neither or both of is_signed and fraction_digits"
            )
        return self

    def set_size_in_bits(self, val: int) -> None:
        super().set_size_in_bits(val)
        if self.size is not None:
            if self.size.is_evaluated() and self.size.value == val:
                return
            raise ClassiqInternalExpansionError("Numeric size mismatch")
        self.size = Expression(expr=str(val))

    @property
    def has_sign(self) -> bool:
        return self.is_signed is not None

    @property
    def sign_value(self) -> bool:
        return False if self.is_signed is None else self.is_signed.to_bool_value()

    @property
    def has_fraction_digits(self) -> bool:
        return self.fraction_digits is not None

    @property
    def fraction_digits_value(self) -> int:
        return (
            0 if self.fraction_digits is None else self.fraction_digits.to_int_value()
        )

    def _update_size_in_bits_from_declaration(self) -> None:
        if (
            self.size is not None
            and self.size.is_evaluated()
            and self.size.is_constant()
        ):
            self._size_in_bits = self.size.to_int_value()

    def get_proxy(self, handle: "HandleBinding") -> QmodQNumProxy:
        return QmodQNumProxy(
            handle,
            size=self.size_in_bits,
            fraction_digits=self.fraction_digits_value,
            is_signed=self.sign_value,
        )

    @property
    def qmod_type_name(self) -> str:
        if (
            self.size is not None
            and (
                self.is_signed is None
                or (self.is_signed.is_evaluated() and not self.is_signed.value.value)
            )
            and (
                self.fraction_digits is None
                or (
                    self.fraction_digits.is_evaluated()
                    and self.fraction_digits.value.value == 0
                )
            )
        ):
            return f"QNum[{self.size.expr}]"
        if (
            self.size is not None
            and self.is_signed is not None
            and self.fraction_digits is not None
        ):
            return f"QNum[{self.size.expr}, {self.is_signed.expr}, {self.fraction_digits.expr}]"
        return "QNum"

    @property
    def raw_qmod_type_name(self) -> str:
        return "QNum"

    @property
    def type_name(self) -> str:
        return "Quantum numeric"

    @property
    def is_instantiated(self) -> bool:
        return self.size is not None

    @property
    def is_evaluated(self) -> bool:
        if self.size is None or not self.size.is_evaluated():
            return False
        if self.is_signed is not None and not self.is_signed.is_evaluated():
            return False
        return not (
            self.fraction_digits is not None and not self.fraction_digits.is_evaluated()
        )

    @property
    def expressions(self) -> list[Expression]:
        exprs = []
        if self.size is not None:
            exprs.append(self.size)
        if self.is_signed is not None:
            exprs.append(self.is_signed)
        if self.fraction_digits is not None:
            exprs.append(self.fraction_digits)
        return exprs

    def get_bounds(self) -> Optional[tuple[float, float]]:
        return self._bounds

    def set_bounds(self, bounds: Optional[tuple[float, float]]) -> None:
        self._bounds = bounds

    def reset_bounds(self) -> None:
        self.set_bounds(None)

    def get_maximal_bounds(self) -> tuple[float, float]:
        return RegisterArithmeticInfo.get_maximal_bounds(
            size=self.size_in_bits,
            is_signed=self.sign_value,
            fraction_places=self.fraction_digits_value,
        )

    def get_effective_bounds(
        self, machine_precision: Optional[int] = None
    ) -> tuple[float, float]:
        bounds = self.get_bounds() or self.get_maximal_bounds()

        if machine_precision is None or machine_precision >= self.fraction_digits_value:
            return bounds
        return (
            number_utils.limit_fraction_places(bounds[0], machine_precision),
            number_utils.limit_fraction_places(bounds[1], machine_precision),
        )

    @property
    def minimal_size_in_bits(self) -> int:
        return self.size_in_bits if self.has_size_in_bits else 1


class RegisterQuantumType(BaseModel):
    quantum_types: "ConcreteQuantumType"
    size: int = Field(default=1)

    @property
    def qmod_type_name(self) -> str:
        try:
            return self.quantum_types.qmod_type_name.split("[")[0]
        except AttributeError:
            return "default"


RegisterQuantumTypeDict = dict[str, RegisterQuantumType]


def register_info_to_quantum_type(reg_info: RegisterArithmeticInfo) -> QuantumNumeric:
    result = QuantumNumeric()
    result.set_size_in_bits(reg_info.size)
    result.is_signed = Expression(expr=str(reg_info.is_signed))
    result.fraction_digits = Expression(expr=str(reg_info.fraction_places))
    result.set_bounds(tuple(reg_info.bounds))  # type: ignore[arg-type]
    return result


UNRESOLVED_SIZE = 1000


def quantum_var_to_register(name: str, qtype: QuantumType) -> RegisterUserInput:
    signed: bool = False
    fraction_places: int = 0
    bounds: Optional[tuple[float, float]] = None
    if isinstance(qtype, QuantumNumeric):
        signed = qtype.sign_value
        fraction_places = qtype.fraction_digits_value
        bounds = qtype.get_bounds()
    return RegisterUserInput(
        name=name,
        size=qtype.size_in_bits if qtype.has_size_in_bits else UNRESOLVED_SIZE,
        is_signed=signed,
        fraction_places=fraction_places,
        bounds=bounds,
    )


def quantum_type_to_register_quantum_type(
    qtype: QuantumType, size: int
) -> RegisterQuantumType:
    return RegisterQuantumType(
        quantum_types=qtype,
        size=size,
    )
