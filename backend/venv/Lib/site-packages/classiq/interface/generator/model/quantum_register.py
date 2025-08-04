import itertools
import sys
from collections.abc import Iterator
from types import GenericAlias as TypesGenericAlias
from typing import (  # type: ignore[attr-defined]
    Any,
    Optional,
    Union,
    _GenericAlias,
)

from classiq.interface.exceptions import ClassiqQRegError
from classiq.interface.generator.arith.register_user_input import (
    RegisterArithmeticInfo,
    RegisterUserInput,
)
from classiq.interface.generator.function_params import ArithmeticIODict, IOName
from classiq.interface.generator.register_role import RegisterRole


# This class is used for QReg, to support type-hint initialization
#   Due to the `size` property of QReg
class QRegGenericAlias(_GenericAlias, _root=True):  # type: ignore[call-arg]
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        arith_info = {}
        if self.size is not None:
            arith_info["size"] = self.size
        if self.fraction_places is not None:
            arith_info["fraction_places"] = self.fraction_places

        return super().__call__(*args, **kwargs, **arith_info)

    def __eq__(self, other: Any) -> bool:
        if sys.version_info >= (3, 9) and isinstance(other, TypesGenericAlias):
            return (
                self.__origin__ == other.__origin__ and self.__args__ == other.__args__
            )
        else:
            return super().__eq__(other)

    @property
    def role(self) -> Optional[RegisterRole]:
        return getattr(self.__origin__, "role", None)

    @property
    def size(self) -> Optional[int]:
        if self.integer_places is not None:
            return self.integer_places + (self.fraction_places or 0)
        return None

    @property
    def integer_places(self) -> Optional[int]:
        if len(self.__args__) in (1, 2) and isinstance(self.__args__[0], int):
            return self.__args__[0]
        return None

    @property
    def fraction_places(self) -> Optional[int]:
        if len(self.__args__) == 2 and isinstance(self.__args__[1], int):
            return self.__args__[1]
        return None


class Qubit:
    pass


class QReg:
    """Represents a logical sequence of qubits.
    The QReg can be used as an `in_wires` or `out_wires` argument to Model function calls,
    assisting in model connectivity.
    """

    def __init__(self, size: int) -> None:
        """Initializes a new QReg with the specified number of qubits.

        Args:
            size: The number of qubits in the QReg.
        """
        if size <= 0:
            raise ClassiqQRegError(f"Cannot create {size} new qubits")
        self._qubits = [Qubit() for _ in range(size)]

    def __hash__(self) -> int:
        return super.__hash__(self)

    @classmethod
    def _from_qubits(cls, qubits: list[Qubit]) -> "QReg":
        if (
            not isinstance(qubits, list)
            or not all(isinstance(qubit, Qubit) for qubit in qubits)
            or len(qubits) == 0
        ):
            raise ClassiqQRegError(f"Cannot create QReg from {qubits}")
        qreg = cls(size=1)
        qreg._qubits = qubits
        return qreg

    def __getitem__(self, key: Union[int, slice]) -> "QReg":
        state = self._qubits[key]
        return QReg._from_qubits(state if isinstance(state, list) else [state])

    def __setitem__(self, key: Union[int, slice], value: "QReg") -> None:
        if isinstance(key, int) and len(value) != 1:
            raise ClassiqQRegError(
                f"Size mismatch: value size {len(value)}, expected size 1"
            )
        self._qubits[key] = value._qubits[0] if isinstance(key, int) else value._qubits  # type: ignore[call-overload]

    def __iter__(self) -> Iterator["QReg"]:
        return iter([self[idx] for idx in range(len(self))])

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, QReg) and self._qubits == other._qubits

    def isoverlapping(self, other: "QReg") -> bool:
        return isinstance(other, QReg) and not set(self._qubits).isdisjoint(
            set(other._qubits)
        )

    @classmethod
    def concat(cls, *qregs: "QReg") -> "QReg":
        """Concatenate two QRegs.

        Args:
            qregs: the QRegs to concat in order, as separate arguments.

        Returns:
            A QReg representing the concatenation of the given QRegs.

        """
        qubits = list(itertools.chain.from_iterable(qreg._qubits for qreg in qregs))
        return cls._from_qubits(qubits)

    def __len__(self) -> int:
        return len(self._qubits)

    @property
    def qubits(self) -> list[Qubit]:
        return self._qubits

    def __class_getitem__(cls, params: Any) -> QRegGenericAlias:
        # Supporting python 3.7+, thus returning `typing._GenericAlias` instead of `types.GenericAlias`
        if isinstance(params, int):
            return QRegGenericAlias(cls, params)

        raise ClassiqQRegError(f"Invalid size: {params} ; int required")

    def to_register_user_input(self, name: str = "") -> RegisterUserInput:
        fraction_places = getattr(self, "fraction_places", 0)
        is_signed = getattr(self, "is_signed", False)
        return RegisterUserInput(
            name=name,
            size=len(self),
            is_signed=is_signed,
            fraction_places=fraction_places,
        )

    @staticmethod
    def from_arithmetic_info(info: RegisterArithmeticInfo) -> "QReg":
        method = _get_qreg_type_from_arithmetic_info(info)
        frac_attr = {"fraction_places": info.fraction_places} if info.is_frac else {}
        return method(size=info.size, **frac_attr)


# QReg with arithmetic properties
class QSFixed(QReg):
    is_signed: bool = True

    def __init__(self, size: int, fraction_places: int) -> None:
        self.fraction_places: int = fraction_places
        super().__init__(size=size)

    def __class_getitem__(cls, params: Any) -> QRegGenericAlias:
        # Supporting python 3.7+, thus returning `typing._GenericAlias` instead of `types.GenericAlias`
        if (
            type(params) is tuple
            and len(params) == 2
            and isinstance(params[0], int)
            and isinstance(params[1], int)
        ):
            return QRegGenericAlias(cls, params)

        raise ClassiqQRegError(f"Invalid info: {params} ; Tuple[int, int] required")


QFixed = QSFixed


class QUFixed(QFixed):
    is_signed: bool = False


class QSInt(QFixed):
    def __init__(self, size: int) -> None:
        super().__init__(size=size, fraction_places=0)

    def __class_getitem__(cls, params: Any) -> QRegGenericAlias:
        # Integers have fraction_places always set to 0,
        # thus, their type hint is identical to that of QReg.
        return super(QSFixed, cls).__class_getitem__(params)


QInt = QSInt


class QUInt(QInt):
    is_signed: bool = False


# QReg with synthesis properties
class ZeroQReg(QReg):
    role: RegisterRole = RegisterRole.ZERO_INPUT
    wire_to_zero: bool = True


class AuxQReg(ZeroQReg):
    role: RegisterRole = RegisterRole.AUXILIARY


_PROP_TO_QREG_TYPE = {
    (False, False): QUInt,
    (False, True): QUFixed,
    (True, False): QSInt,
    (True, True): QSFixed,
}


def _get_qreg_type_from_arithmetic_info(info: RegisterArithmeticInfo) -> type["QReg"]:
    return _PROP_TO_QREG_TYPE[(info.is_signed, info.is_frac)]


def _get_qreg_generic_alias_from_arithmetic_info(
    info: RegisterArithmeticInfo,
) -> QRegGenericAlias:
    qreg_type = _get_qreg_type_from_arithmetic_info(info=info)
    if info.fraction_places == 0:
        return QRegGenericAlias(qreg_type, info.size)
    params = (info.size - info.fraction_places, info.fraction_places)
    return QRegGenericAlias(qreg_type, params)


def get_type_and_size_dict(
    arithmetic_info_dict: ArithmeticIODict,
) -> dict[IOName, QRegGenericAlias]:
    return {
        io_name: _get_qreg_generic_alias_from_arithmetic_info(info)
        for io_name, info in arithmetic_info_dict.items()
    }


__all__ = [
    "AuxQReg",
    "QReg",
    "QSFixed",
    "QSInt",
    "QUFixed",
    "QUInt",
    "ZeroQReg",
]
