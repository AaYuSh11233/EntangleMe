from enum import IntEnum
from typing import TYPE_CHECKING

from classiq.interface.generator.types.enum_declaration import EnumDeclaration

if TYPE_CHECKING:
    from classiq.qmod.builtins.structs import SparsePauliOp


class Element(IntEnum):
    H = 0
    He = 1
    Li = 2
    Be = 3
    B = 4
    C = 5
    N = 6
    O = 7  # noqa: E741
    F = 8
    Ne = 9
    Na = 10
    Mg = 11
    Al = 12
    Si = 13
    P = 14
    S = 15
    Cl = 16
    Ar = 17
    K = 18
    Ca = 19
    Sc = 20
    Ti = 21
    V = 22
    Cr = 23
    Mn = 24
    Fe = 25
    Co = 26
    Ni = 27
    Cu = 28
    Zn = 29
    Ga = 30
    Ge = 31
    As = 32
    Se = 33
    Br = 34
    Kr = 35
    Rb = 36
    Sr = 37
    Y = 38
    Zr = 39
    Nb = 40
    Mo = 41
    Tc = 42
    Ru = 43
    Rh = 44
    Pd = 45
    Ag = 46
    Cd = 47
    In = 48
    Sn = 49
    Sb = 50
    Te = 51
    I = 52  # noqa: E741
    Xe = 53
    Cs = 54
    Ba = 55
    La = 56
    Ce = 57
    Pr = 58
    Nd = 59
    Pm = 60
    Sm = 61
    Eu = 62
    Gd = 63
    Tb = 64
    Dy = 65
    Ho = 66
    Er = 67
    Tm = 68
    Yb = 69
    Lu = 70
    Hf = 71
    Ta = 72
    W = 73
    Re = 74
    Os = 75
    Ir = 76
    Pt = 77
    Au = 78
    Hg = 79
    Tl = 80
    Pb = 81
    Bi = 82
    Po = 83
    At = 84
    Rn = 85
    Fr = 86
    Ra = 87
    Ac = 88
    Th = 89
    Pa = 90
    U = 91
    Np = 92
    Pu = 93
    Am = 94
    Cm = 95
    Bk = 96
    Cf = 97
    Es = 98
    Fm = 99
    Md = 100
    No = 101
    Lr = 102
    Rf = 103
    Db = 104
    Sg = 105
    Bh = 106
    Hs = 107
    Mt = 108
    Ds = 109
    Rg = 110
    Cn = 111
    Nh = 112
    Fl = 113
    Mc = 114
    Lv = 115
    Ts = 116
    Og = 117


class FermionMapping(IntEnum):
    JORDAN_WIGNER = 0
    PARITY = 1
    BRAVYI_KITAEV = 2
    FAST_BRAVYI_KITAEV = 3


class FinanceFunctionType(IntEnum):
    VAR = 0
    SHORTFALL = 1
    X_SQUARE = 2
    EUROPEAN_CALL_OPTION = 3


class LadderOperator(IntEnum):
    PLUS = 0
    MINUS = 1


class Optimizer(IntEnum):
    COBYLA = 1
    SPSA = 2
    L_BFGS_B = 3
    NELDER_MEAD = 4
    ADAM = 5
    SLSQP = 6


class Pauli(IntEnum):
    """
    Enumeration for the Pauli matrices used in quantum computing.

    The Pauli matrices are fundamental operations in quantum computing, and this
    enum assigns integer values to represent each matrix.
    """

    I = 0  # noqa: E741
    """I (int): Identity matrix, represented by the integer 0. \n
    $I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}$"""

    X = 1
    """X (int): Pauli-X matrix, represented by the integer 1. \n
    $X = \\begin{bmatrix} 0 & 1 \\\\ 1 & 0 \\end{bmatrix}$"""

    Y = 2
    """Y (int): Pauli-Y matrix, represented by the integer 2. \n
    $Y = \\begin{bmatrix} 0 & -i \\\\ i & 0 \\end{bmatrix}$"""

    Z = 3
    """Z (int): Pauli-Z matrix, represented by the integer 3. \n
    $Z = \\begin{bmatrix} 1 & 0 \\\\ 0 & -1 \\end{bmatrix}$"""

    def __call__(self, index: int) -> "SparsePauliOp":
        from classiq.qmod.builtins.structs import (
            IndexedPauli,
            SparsePauliOp,
            SparsePauliTerm,
        )

        return SparsePauliOp(
            terms=[
                SparsePauliTerm(
                    paulis=[  # type:ignore[arg-type]
                        IndexedPauli(pauli=self, index=index)  # type:ignore[arg-type]
                    ],
                    coefficient=1.0,  # type:ignore[arg-type]
                )
            ],
            num_qubits=index + 1,
        )


class QSVMFeatureMapEntanglement(IntEnum):
    FULL = 0
    LINEAR = 1
    CIRCULAR = 2
    SCA = 3
    PAIRWISE = 4


BUILTIN_ENUM_DECLARATIONS = {
    enum_def.__name__: EnumDeclaration(
        name=enum_def.__name__,
        members={enum_val.name: enum_val.value for enum_val in enum_def},
    )
    for enum_def in vars().values()
    if (
        isinstance(enum_def, type)
        and issubclass(enum_def, IntEnum)
        and enum_def is not IntEnum
    )
}

__all__ = [
    "Element",
    "FermionMapping",
    "FinanceFunctionType",
    "LadderOperator",
    "Optimizer",
    "Pauli",
    "QSVMFeatureMapEntanglement",
]
