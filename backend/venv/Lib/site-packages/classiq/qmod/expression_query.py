from typing import TYPE_CHECKING

from classiq.interface.generator.arith.arithmetic import compute_arithmetic_result_type
from classiq.interface.generator.arith.number_utils import MAXIMAL_MACHINE_PRECISION
from classiq.interface.model.quantum_type import QuantumNumeric

from classiq.qmod.qmod_variable import QNum
from classiq.qmod.symbolic_type import SymbolicTypes


def get_expression_numeric_attributes(
    vars: list[QNum],
    expr: SymbolicTypes,
    machine_precision: int = MAXIMAL_MACHINE_PRECISION,
) -> tuple[int, bool, int]:
    """
    Computes and returns the numeric attributes of a given symbolic expression.

    Args:
        vars: A list of `QNum` variables used in the symbolic expression.
        expr: The symbolic expression for which numeric attributes are to be computed.
        machine_precision: The precision level of the machine for the computation. Defaults to MAXIMAL_MACHINE_PRECISION = 20.

    Returns:
        Tuple[int, bool, int]:
            A tuple containing the following numeric attributes:
            - The size in bits (int) required to represent the result.
            - A boolean indicating whether the result is signed (bool).
            - The number of fraction digits (int) in the result.

    """
    res_type = compute_arithmetic_result_type(
        expr_str=str(expr),
        var_types={str(var.get_handle_binding()): var.get_qmod_type() for var in vars},
        machine_precision=machine_precision,
    )
    if TYPE_CHECKING:
        assert isinstance(res_type, QuantumNumeric)
    return res_type.size_in_bits, res_type.sign_value, res_type.fraction_digits_value
