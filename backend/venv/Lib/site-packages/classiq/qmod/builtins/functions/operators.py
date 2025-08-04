from classiq.qmod.qfunc import qfunc
from classiq.qmod.quantum_callable import QCallable, QCallableList


@qfunc(external=True)
def permute(
    functions: QCallableList,
) -> None:
    pass


@qfunc(external=True)
def apply(
    operand: QCallable,
) -> None:
    pass
