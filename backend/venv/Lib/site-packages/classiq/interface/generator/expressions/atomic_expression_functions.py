SUPPORTED_PYTHON_BUILTIN_FUNCTIONS = {"len", "sum", "print"}

CLASSIQ_BUILTIN_CLASSICAL_FUNCTIONS = {
    "hypercube_entangler_graph",
    "grid_entangler_graph",
    "qft_const_adder_phase",
    "log_normal_finance_post_process",
    "gaussian_finance_post_process",
    "molecule_problem_to_hamiltonian",
    "fock_hamiltonian_problem_to_hamiltonian",
    "molecule_ground_state_solution_post_process",
}

CLASSIQ_EXPR_FUNCTIONS = {
    "do_div",
    "do_slice",
    "do_subscript",
    "get_type",
    "struct_literal",
    "get_field",
}

MEASUREMENT_FUNCTIONS = {
    "measure",
}

SUPPORTED_CLASSIQ_BUILTIN_FUNCTIONS = {
    *CLASSIQ_BUILTIN_CLASSICAL_FUNCTIONS,
    *CLASSIQ_EXPR_FUNCTIONS,
    *MEASUREMENT_FUNCTIONS,
}

SUPPORTED_CLASSIQ_SYMPY_WRAPPERS = {
    "BitwiseAnd",
    "BitwiseXor",
    "BitwiseNot",
    "BitwiseOr",
    "LogicalXor",
    "RShift",
    "LShift",
    "mod_inverse",
    "min",
    "Min",
    "max",
    "Max",
}

SUPPORTED_ATOMIC_EXPRESSION_FUNCTIONS = {
    *SUPPORTED_CLASSIQ_BUILTIN_FUNCTIONS,
    *SUPPORTED_CLASSIQ_SYMPY_WRAPPERS,
    *SUPPORTED_PYTHON_BUILTIN_FUNCTIONS,
}

CLASSICAL_ATTRIBUTES = {"len", "size", "is_signed", "fraction_digits"}
SUPPORTED_ATOMIC_EXPRESSION_FUNCTIONS_QMOD = (
    SUPPORTED_ATOMIC_EXPRESSION_FUNCTIONS - CLASSICAL_ATTRIBUTES
)
