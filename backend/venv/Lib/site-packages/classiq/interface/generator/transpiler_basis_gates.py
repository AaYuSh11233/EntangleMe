from typing import TYPE_CHECKING, Optional

from typing_extensions import TypeAlias

from classiq.interface.enum_utils import StrEnum

BasisGates: TypeAlias = frozenset[str]

SINGLE_QUBIT_GATES: BasisGates = frozenset(
    (
        "u1",
        "u2",
        "u",
        "p",
        "x",
        "y",
        "z",
        "t",
        "tdg",
        "s",
        "sdg",
        "sx",
        "sxdg",
        "rx",
        "ry",
        "rz",
        "id",
        "h",
        "r",
    )
)

BASIC_TWO_QUBIT_GATES: BasisGates = frozenset(
    (
        "cx",
        "cy",
        "cz",
    )
)

EXTRA_TWO_QUBIT_GATES: BasisGates = frozenset(
    (
        "swap",
        "ecr",
        "rxx",
        "ryy",
        "rzz",
        "rzx",
        "crx",
        "cry",
        "crz",
        "csx",
        "cu1",
        "cu",
        "ch",
        "cp",
    )
)

TWO_QUBIT_GATES = BASIC_TWO_QUBIT_GATES | EXTRA_TWO_QUBIT_GATES

THREE_QUBIT_GATES: BasisGates = frozenset(("ccx", "cswap"))
DEFAULT_BASIS_GATES: BasisGates = SINGLE_QUBIT_GATES | BASIC_TWO_QUBIT_GATES
ALL_GATES: BasisGates = SINGLE_QUBIT_GATES | TWO_QUBIT_GATES | THREE_QUBIT_GATES

ROUTING_TWO_QUBIT_BASIS_GATES: BasisGates = frozenset(
    ("cx", "ecr", "rzx", "ryy", "rxx", "rzz", "cy", "cz", "cp", "swap")
)
DEFAULT_ROUTING_BASIS_GATES: BasisGates = SINGLE_QUBIT_GATES | frozenset(("cx",))
# The Enum names are capitalized per recommendation in https://docs.python.org/3/library/enum.html#module-enum
# The Enum values are lowered to keep consistency
# The super class for the builtin gates ensures being a string subtype

ALL_GATES_DICT = {gate.upper(): gate.lower() for gate in sorted(ALL_GATES)}


class LowerValsEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if not isinstance(value, str):
            return None
        lower = value.lower()
        if value == lower:
            return None
        return cls(lower)


if TYPE_CHECKING:
    # A subset of the gates for better type checking
    class TranspilerBasisGates(StrEnum):
        """
        A subset of the gates used in the transpiler.
        """

        X = "x"
        CX = "cx"
        CZ = "cz"
        T = "T"
        U = "u"
        Z = "z"
        RX = "rx"
        RY = "ry"
        RZ = "rz"
        SX = "sx"
        H = "h"

else:
    TranspilerBasisGates = LowerValsEnum("TranspilerBasisGates", ALL_GATES_DICT)
