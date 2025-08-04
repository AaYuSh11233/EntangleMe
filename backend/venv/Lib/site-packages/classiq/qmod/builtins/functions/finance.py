from typing import Literal

from classiq.qmod.builtins.structs import (
    FinanceFunction,
    GaussianModel,
    LogNormalModel,
)
from classiq.qmod.qfunc import qfunc
from classiq.qmod.qmod_variable import QArray, QBit


@qfunc(external=True)
def log_normal_finance(
    finance_model: LogNormalModel,
    finance_function: FinanceFunction,
    func_port: QArray[QBit, Literal["get_field(finance_model, 'num_qubits')"]],
    obj_port: QBit,
) -> None:
    pass


@qfunc(external=True)
def gaussian_finance(
    finance_model: GaussianModel,
    finance_function: FinanceFunction,
    func_port: QArray[
        QBit,
        Literal[
            "get_field(finance_model, 'num_qubits') + get_field(get_field(finance_model, 'rhos'), 'len') + floor(log(sum(get_field(finance_model, 'loss')), 2)) + 1"
        ],
    ],
    obj_port: QBit,
) -> None:
    pass
