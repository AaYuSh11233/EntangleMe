import functools
from typing import Any, Optional, get_args

from sympy import (
    Array,
    Basic,
    Expr,
    Float,
    Integer,
    Matrix,
    Piecewise,
    Rational,
    Symbol,
)
from sympy.logic.boolalg import BooleanAtom
from sympy.printing.pycode import PythonCodePrinter

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.expression_types import ExpressionValue
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)

from classiq.evaluators.qmod_expression_visitors.sympy_wrappers import LogicalXor


def sympy_to_python(
    value: Any, locals: Optional[dict[str, ExpressionValue]] = None
) -> ExpressionValue:
    if isinstance(value, AnyClassicalValue):
        pass
    elif isinstance(value, Integer):
        value = int(value)
    elif isinstance(value, Float):
        value = float(value)
    elif isinstance(value, BooleanAtom):
        value = bool(value)
    elif isinstance(value, Array):
        value = sympy_to_python(value.tolist(), locals)
    elif isinstance(value, Rational):
        value = float(value.evalf())
    elif isinstance(value, list):
        value = [sympy_to_python(element, locals) for element in value]
    elif isinstance(value, Matrix):
        value = [sympy_to_python(element, locals) for element in value.tolist()]
    elif isinstance(value, Symbol) and locals is not None and value.name in locals:
        return locals[value.name]
    if value is None:
        value = False

    if not isinstance(value, get_args(ExpressionValue)):
        raise ClassiqInternalExpansionError(
            f"Invalid evaluated expression {value} of type {type(value)}"
        )

    return value


def _conditional_true(*args: Any, **kwargs: Any) -> bool:
    return True


class SympyToQuantumExpressionTranslator(PythonCodePrinter):
    _operators = {**PythonCodePrinter._operators, **{"not": "~", "xor": "^"}}
    _kf = {
        **PythonCodePrinter._kf,
        **{"max": "max", "min": "min", "Max": "max", "Min": "min"},
    }
    BINARY_BITWISE_OPERATORS_MAPPING = {
        "BitwiseAnd": "&",
        "BitwiseOr": "|",
        "BitwiseXor": "^",
        "LogicalXor": "^",
        "RShift": ">>",
        "LShift": "<<",
    }
    UNARY_BITWISE_OPERATORS_MAPPING = {"BitwiseNot": "~"}

    @staticmethod
    def _print_bitwise_binary_operator(
        left_arg: Expr, right_arg: Expr, operator: str
    ) -> str:
        return f"(({left_arg}) {operator} ({right_arg}))"

    @staticmethod
    def _print_bitwise_unary_operator(arg: Expr, operator: str) -> str:
        return f"({operator} ({arg}))"

    def __init__(self) -> None:
        super().__init__(settings={"fully_qualified_modules": False})
        for binary_operator in self.BINARY_BITWISE_OPERATORS_MAPPING:
            self.known_functions[binary_operator] = [
                (
                    _conditional_true,
                    functools.partial(
                        self._print_bitwise_binary_operator,
                        operator=self.BINARY_BITWISE_OPERATORS_MAPPING[binary_operator],
                    ),
                )
            ]
        for unary_operator in self.UNARY_BITWISE_OPERATORS_MAPPING:
            self.known_functions[unary_operator] = [
                (
                    _conditional_true,
                    functools.partial(
                        self._print_bitwise_unary_operator,
                        operator=self.UNARY_BITWISE_OPERATORS_MAPPING[unary_operator],
                    ),
                )
            ]

    def _print_Piecewise(self, expr: Piecewise) -> str:  # noqa: N802
        return str(expr)

    def _print_LogicalXor(self, expr: LogicalXor) -> str:  # noqa: N802
        return f"(({self._print(expr.args[0])}) ^ ({self._print(expr.args[1])}))"


class SympyToBoolExpressionTranslator(SympyToQuantumExpressionTranslator):
    _operators = {
        **SympyToQuantumExpressionTranslator._operators,
        **{"not": "not ", "xor": "xor"},
    }


def translate_sympy_quantum_expression(expr: Basic, preserve_bool_ops: bool) -> str:
    if isinstance(expr, AnyClassicalValue):
        return str(expr)
    if preserve_bool_ops:
        return SympyToBoolExpressionTranslator().doprint(expr)
    else:
        return SympyToQuantumExpressionTranslator().doprint(expr)
