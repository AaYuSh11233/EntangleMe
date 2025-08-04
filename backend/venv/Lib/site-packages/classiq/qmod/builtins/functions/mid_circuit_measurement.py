from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QBit


@qfunc(external=True)
def RESET(target: QBit) -> None:
    """
    Resets the target qubit to the |0> state.

    Performed by measuring the qubit and applying an X gate if necessary.

    Args:
        target: the qubit to reset

    Notes:
        We approximate the depth of a single RESET gate to 1000 X gates.
    """
    pass
