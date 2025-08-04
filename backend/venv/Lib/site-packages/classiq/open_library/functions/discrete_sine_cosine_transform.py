from classiq.open_library.functions.qft_functions import qft
from classiq.open_library.functions.utility_functions import apply_to_all
from classiq.qmod.builtins.functions.standard_gates import PHASE, H, S, X, Z
from classiq.qmod.builtins.operations import (
    allocate,
    bind,
    control,
    inplace_add,
    invert,
    repeat,
    within_apply,
)
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import Const, Permutable, QArray, QBit, QNum
from classiq.qmod.symbolic import pi


def _b_operator(q: QBit) -> None:
    S(q)
    H(q)


@qfunc
def _qct_d_operator(x: Const[QNum], q: QBit) -> None:
    _b_operator(q)
    control(x == 0, lambda: invert(lambda: _b_operator(q)))


@qfunc
def _qct_pi_operator(x: Permutable[QArray[QBit]], q: Const[QBit]) -> None:
    control(
        q == 1,
        lambda: [
            apply_to_all(X, x),
            inplace_add(1, x),  # type:ignore[arg-type]
        ],
    )


def _t_operator(x: QArray) -> None:
    _qct_d_operator(x[0 : x.len - 1], x[x.len - 1])
    _qct_pi_operator(x[0 : x.len - 1], x[x.len - 1])


def _vn_operator(x: QArray[QBit], q: QBit) -> None:
    H(q)
    control(q == 1, lambda: apply_to_all(X, x))


def _d1_operator(x: QArray[QBit], q: QBit) -> None:
    omega_exp = 2 * pi / (4 * 2**x.len)

    # Li
    control(q == 0, lambda: repeat(x.len, lambda k: PHASE(omega_exp * (2**k), x[k])))
    # Ki
    control(
        q == 1,
        lambda: repeat(
            x.len,
            lambda k: within_apply(
                lambda: X(x[k]), lambda: PHASE(-omega_exp * (2**k), x[k])
            ),
        ),
    )
    PHASE(-omega_exp, q)


def _pi2_operator(x: QArray[QBit], q: QBit) -> None:
    control(q == 1, lambda: inplace_add(1, x))  # type:ignore[arg-type]


def _j_operator(q: QBit) -> None:
    within_apply(lambda: Z(q), lambda: (S(q), H(q), S(q)))


def _b_t_operator(q: QBit) -> None:
    H(q)
    S(q)


def _d0dt_operator(x: QArray, q: QBit) -> None:
    x_num: QNum = QNum(size=x.len)
    bind(x, x_num)
    _b_t_operator(q)
    control(x_num == 0, lambda: _j_operator(q))
    bind(x_num, x)


def _un_dag_operator(x: QArray[QBit], q: QBit) -> None:
    _d1_operator(x, q)
    invert(lambda: _qct_pi_operator(x, q))
    _d0dt_operator(x, q)
    invert(lambda: _pi2_operator(x, q))


@qfunc
def qct_qst_type1(x: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the quantum discrete cosine (DCT) and sine (DST)
    transform of type 1 to the qubit array `x`.
    Corresponds to the matrix (with $n\\equiv$`x.len`):

    $$
    \\left(
    \begin{array}{ccc|c}
    {} &{} &{} \\
      {}&{\rm DCT}^{(1)}(2^{n-1}+1) & {}& 0\\
      {} &{} &{} \\
      \\hline
      {} & 0 & {} & i{\rm DST}^{(1)}(2^{n-1}-1)
    \\end{array}
    \right)
    $$

    Args:
        x: The qubit array to apply the transform to.
    """
    within_apply(lambda: _t_operator(x), lambda: qft(x))


@qfunc(unchecked=["q"])
def qct_qst_type2(x: QArray[QBit], q: Const[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the quantum discrete cosine (DCT) and sine (DST)
    transform of type 2 to the qubit array `x` concatenated with `q`, with `q` being the MSB.
    Corresponds to the matrix (with $n\\equiv$`x.len`+1):

    $$
    \\left(
    \begin{array}{c|c}
      {\rm DCT}^{(2)}(2^{n-1}) & 0\\
      \\hline
      0 & -{\rm DST}^{(2)}(2^{n-1})
    \\end{array}
    \right)
    $$

    Args:
        x: The LSB part of the qubit array to apply the transform to.
        q: The MSB of the qubit array to apply the transform to.
    """
    extended_state: QArray = QArray()
    _vn_operator(x, q)
    bind([x, q], extended_state)
    qft(extended_state)
    bind(extended_state, [x, q])
    _un_dag_operator(x, q)


@qfunc
def qct_type2(x: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the quantum discrete cosine (DCT)
    transform of type 2, ${\rm DCT}^{(2)}$, to the qubit array `x`.

    Args:
        x: The qubit array to apply the transform to.
    """
    q = QBit()
    within_apply(lambda: allocate(q), lambda: qct_qst_type2(x, q))


@qfunc
def qst_type2(x: QArray[QBit]) -> None:
    """
    [Qmod Classiq-library function]

    Applies the quantum discrete sine (DST)
    transform of type 2, ${\rm DST}^{(2)}$, to the qubit array `x`.

    Args:
        x: The qubit array to apply the transform to.
    """
    q = QBit()
    within_apply(
        lambda: (allocate(q), X(q)),
        lambda: qct_qst_type2(x, q),
    )
