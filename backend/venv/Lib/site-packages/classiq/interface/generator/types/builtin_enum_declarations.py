# This file was generated automatically - do not edit manually


from enum import IntEnum


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
    I = 0  # noqa: E741
    X = 1
    Y = 2
    Z = 3


class QSVMFeatureMapEntanglement(IntEnum):
    FULL = 0
    LINEAR = 1
    CIRCULAR = 2
    SCA = 3
    PAIRWISE = 4


__all__ = [
    "Element",
    "FermionMapping",
    "FinanceFunctionType",
    "LadderOperator",
    "Optimizer",
    "Pauli",
    "QSVMFeatureMapEntanglement",
]
