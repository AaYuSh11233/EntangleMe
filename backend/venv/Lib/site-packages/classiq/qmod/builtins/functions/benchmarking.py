from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_parameter import CInt
from classiq.qmod.qmod_variable import QArray, QBit


@qfunc(external=True)
def randomized_benchmarking(num_of_cliffords: CInt, target: QArray[QBit]) -> None:
    pass
