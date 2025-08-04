BASIC_ARITHMETIC_OPERATORS: list[str] = ["+", "-", "*", "/", "%"]
MATHEMATICAL_FUNCTIONS: list[str] = [
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "asin",
    "acos",
    "atan",
    "acot",
    "asec",
    "acsc",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "sech",
    "csch",
    "asinh",
    "acosh",
    "atanh",
    "acoth",
    "asech",
    "exp",
    "log",
    "ln",
    "sqrt",
    "abs",
    "floor",
    "ceiling",
    "Max",
    "Min",
    "mod_inverse",
    "Mod",
]
SPECIAL_FUNCTIONS: list[str] = [
    "erf",
    "erfc",
    "gamma",
    "beta",
    "besselj",
    "bessely",
    "besseli",
    "besselk",
    "dirichlet_eta",
    "polygamma",
    "loggamma",
    "factorial",
    "binomial",
    "subfactorial",
    "primorial",
    "bell",
    "bernoulli",
    "euler",
    "catalan",
]
PIECEWISE_FUNCTIONS: list[str] = ["Piecewise", "Heaviside"]
NUMERIC_CONSTANTS: list[str] = [
    "pi",
    "E",
    "I",
    "GoldenRatio",
    "EulerGamma",
    "Catalan",
]
BOOLEAN_CONSTANTS: list[str] = ["true", "false"]
CONSTANTS: list[str] = NUMERIC_CONSTANTS + BOOLEAN_CONSTANTS

DATA_TYPES: list[str] = ["Matrix"]
LOGIC_OPERATORS: list[str] = [
    "And",
    "Or",
    "Not",
    "Xor",
    "Equivalent",
    "Implies",
    "Nand",
    "Nor",
]
RELATIONAL_OPERATORS: list[str] = ["<", "<=", ">", ">=", "!=", "<>", "Eq", "Ne"]

SYMPY_SUPPORTED_EXPRESSIONS: list[str] = (
    BASIC_ARITHMETIC_OPERATORS
    + MATHEMATICAL_FUNCTIONS
    + SPECIAL_FUNCTIONS
    + PIECEWISE_FUNCTIONS
    + CONSTANTS
    + LOGIC_OPERATORS
    + RELATIONAL_OPERATORS
    + DATA_TYPES
)
