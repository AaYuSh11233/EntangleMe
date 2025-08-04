import pyomo
import sympy as sp
from pyomo.core.base.var import VarData

from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.exceptions import ClassiqCombOptNotSupportedProblemError
from classiq.interface.helpers import custom_pydantic_types

from classiq.applications.combinatorial_helpers import memory
from classiq.applications.combinatorial_helpers.memory import InternalQuantumReg
from classiq.applications.combinatorial_helpers.sympy_utils import (
    sympyify_expression,
    sympyify_vars,
)

PYOMO_PARSING_ERROR_MESAGE = "Parsing of this pyomo model is not supported."


def convert_pyomo_to_hamiltonian(
    pyomo_expr: pyomo.core.Expression,
    ordered_pyomo_vars: list[VarData],
    qregs: list[InternalQuantumReg],
) -> PauliOperator:
    symbols_map = sympyify_vars(ordered_pyomo_vars)
    sympy_expr = sympyify_expression(pyomo_expr, symbols_map)
    if not sympy_expr.is_polynomial():
        raise ClassiqCombOptNotSupportedProblemError(PYOMO_PARSING_ERROR_MESAGE)

    ordered_sympy_vars = [
        symbols_map.pyomo2sympy[pyomo_var] for pyomo_var in ordered_pyomo_vars
    ]
    ising_expr = _to_ising_symbolic_objective_function(sympy_expr)
    ising_expr = _refine_ising_expr(ising_expr)

    operator = _convert_ising_sympy_to_operator(ising_expr, ordered_sympy_vars)
    operator = _add_auxiliary_qubits_to_operator(operator, qregs)

    return PauliOperator(pauli_list=operator)


def _convert_ising_sympy_to_operator(
    ising_expr: sp.Expr, ordered_sympy_vars: list[sp.Symbol]
) -> custom_pydantic_types.PydanticPauliList:
    pauli_op_list: custom_pydantic_types.PydanticPauliList = []
    for expr_term in ising_expr.args:
        expr_vars = _get_vars(expr_term)
        z_vec = _find_sub_list_items(ordered_sympy_vars, expr_vars)
        pauli_string_list = ["I"] * len(z_vec)
        for index, is_z_op in enumerate(z_vec):
            if is_z_op:
                pauli_string_list[len(z_vec) - index - 1] = (
                    "Z"  # reminder: Pauli reverses the order!
                )
        pauli_string = "".join(pauli_string_list)
        coeff = _get_coeff_from_expr(expr_term)
        pauli_op_list.append((pauli_string, complex(coeff)))
    return pauli_op_list


def _refine_ising_expr(ising_expr: sp.Expr) -> sp.Expr:
    # The variables here are assumed to be either 1 or -1 (ising variables).
    # Therefore x^a can replaced with 1 if a is even, and with x is a is odd.
    # Change the expression recursively.
    def update_expr(expr: sp.Expr) -> sp.Expr:
        if isinstance(expr, sp.Pow):
            if expr.args[1] % 2:  # odd power: x**a -> x
                expr = expr.args[0]
            else:  # even power: x**a -> 1
                expr = sp.Float(1)
        if hasattr(expr, "args") and expr.args:
            new_args = [update_expr(arg) for arg in expr.args]
            expr_class = type(expr)
            return expr_class(*new_args)
        else:
            return expr

    return update_expr(ising_expr)


def _to_ising_symbolic_objective_function(objective: sp.Expr) -> sp.Expr:
    # cost-function to Hamiltonian conversion explanation:
    # https://qiskit.org/textbook/ch-applications/qaoa.html#1.1-Diagonal-Hamiltonians
    subs_vars_dict = {var: (1 - var) / 2 for var in objective.free_symbols}
    objective_ising = objective.subs(subs_vars_dict)
    return sp.expand(objective_ising)


def _get_vars(expr_term: sp.AtomicExpr) -> list[sp.Symbol]:
    if isinstance(expr_term, sp.Symbol):
        return [expr_term]
    else:
        return expr_term.args


def _find_sub_list_items(
    long_list: list[sp.Symbol], sub_list: list[sp.Symbol]
) -> list[bool]:
    return [x in sub_list for x in long_list]


def _get_coeff_from_expr(expr: sp.Expr) -> float:
    if isinstance(expr, sp.Number):
        return float(expr)
    if isinstance(expr, sp.Symbol):
        return 1
    if all(isinstance(arg, sp.Symbol) for arg in expr.args):
        return 1
    return float(expr.args[0])


def _add_auxiliary_qubits_to_operator(
    operator: custom_pydantic_types.PydanticPauliList, qregs: list[InternalQuantumReg]
) -> custom_pydantic_types.PydanticPauliList:
    # TODO: handle the case when the auxiliary are in the middle of the circuit
    for qreg in qregs:
        if qreg.name == memory.AUXILIARY_NAME:
            operator = [
                ("I" * qreg.size + monomial[0], monomial[1]) for monomial in operator
            ]
    return operator
