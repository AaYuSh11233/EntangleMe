import ast
from typing import Any, Final, Optional, cast

import networkx as nx
import pydantic
from pydantic_core.core_schema import ValidationInfo

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith import arithmetic_expression_parser
from classiq.interface.generator.arith.arithmetic_expression_abc import (
    ArithmeticExpressionABC,
)
from classiq.interface.generator.arith.arithmetic_expression_validator import (
    is_constant,
)
from classiq.interface.generator.arith.arithmetic_param_getters import (
    id2op,
    operation_allows_target,
)
from classiq.interface.generator.arith.arithmetic_result_builder import (
    ArithmeticResultBuilder,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.expression_constants import (
    BOOLEAN_LITERALS,
)
from classiq.interface.model.quantum_type import (
    QuantumNumeric,
    QuantumType,
    quantum_var_to_register,
    register_info_to_quantum_type,
)

ARITHMETIC_EXPRESSION_TARGET_NAME: Final[str] = "arithmetic_target"
ARITHMETIC_EXPRESSION_RESULT_NAME: Final[str] = "expression_result"
ARITHMETIC_EXPRESSION_GARBAGE_NAME: Final[str] = "expression_garbage"

TARGET_ASSIGNMENT_ERROR = "Expression does not support target assignment"


def is_zero(expr: str) -> bool:
    return is_constant(expr) and float(expr) == 0


def is_bool(expr: str) -> bool:
    return expr in BOOLEAN_LITERALS


class Arithmetic(ArithmeticExpressionABC):
    target: Optional[RegisterArithmeticInfo] = None
    inputs_to_save: set[str] = pydantic.Field(default_factory=set)

    @pydantic.field_validator("inputs_to_save")
    @classmethod
    def _validate_inputs_to_save(
        cls, inputs_to_save: set[str], info: ValidationInfo
    ) -> set[str]:
        assert all(reg in info.data.get("definitions", {}) for reg in inputs_to_save)
        return inputs_to_save

    @staticmethod
    def _validate_expression_graph(graph: nx.DiGraph, values: dict[str, Any]) -> None:
        target = values.get("target")
        if target is None:
            return

        # Check that the expression graph allows setting the target of the expression
        if not all(
            degree or operation_allows_target(id2op(node))
            for node, degree in graph.out_degree
        ):
            raise ClassiqValueError(TARGET_ASSIGNMENT_ERROR)

    def _create_ios(self) -> None:
        self._inputs = {
            name: register
            for name, register in self.definitions.items()
            if name in self._get_literal_set()
            and isinstance(register, RegisterArithmeticInfo)
        }
        self._outputs = {
            name: self._inputs[name]
            for name in self.inputs_to_save
            if name in self._inputs
        }
        # TODO: avoid calling the result builder again, as it is called in validation
        result_builder = ArithmeticResultBuilder(
            graph=arithmetic_expression_parser.parse_expression(self.expression),
            definitions=self.definitions,
            machine_precision=self.machine_precision,
        )
        self._outputs[ARITHMETIC_EXPRESSION_RESULT_NAME] = result_builder.result
        if result_builder.garbage:
            self._outputs[ARITHMETIC_EXPRESSION_GARBAGE_NAME] = result_builder.garbage
        if self.target:
            self._inputs[ARITHMETIC_EXPRESSION_TARGET_NAME] = self.target


def get_arithmetic_params(
    expr_str: str,
    var_types: dict[str, QuantumType],
    machine_precision: int,
    enable_target: bool = False,
) -> Arithmetic:
    expr_str, var_types = _substitute_quantum_subscripts(
        expr_str, var_types, machine_precision
    )
    return Arithmetic(
        expression=expr_str,
        definitions={
            name: quantum_var_to_register(name, qtype)
            for name, qtype in var_types.items()
        },
        inputs_to_save=set(var_types.keys()),
        # FIXME: generalize inout target to multiple qubits
        target=RegisterArithmeticInfo(size=1) if enable_target else None,
        machine_precision=machine_precision,
    )


def compute_arithmetic_result_type(
    expr_str: str, var_types: dict[str, QuantumType], machine_precision: int
) -> QuantumNumeric:
    one_qbit_qnum = QuantumNumeric(
        size=Expression(expr="1"),
        is_signed=Expression(expr="False"),
        fraction_digits=Expression(expr="0"),
    )
    if is_zero(expr_str):
        one_qbit_qnum.set_bounds((0, 0))
        return one_qbit_qnum
    if is_bool(expr_str):
        return one_qbit_qnum
    arith_param = get_arithmetic_params(expr_str, var_types, machine_precision)
    return register_info_to_quantum_type(
        arith_param.outputs[ARITHMETIC_EXPRESSION_RESULT_NAME]
    )


def aggregate_numeric_types(
    numeric_types: list[QuantumNumeric],
) -> RegisterArithmeticInfo:
    if all(
        numeric_type.size_in_bits == 1
        and numeric_type.sign_value
        and numeric_type.fraction_digits_value == 1
        for numeric_type in numeric_types
    ):
        return RegisterArithmeticInfo(size=1, is_signed=True, fraction_places=1)
    int_size = max(
        numeric_type.size_in_bits
        - int(numeric_type.sign_value)
        - numeric_type.fraction_digits_value
        for numeric_type in numeric_types
    )
    is_signed = any(numeric_type.sign_value for numeric_type in numeric_types)
    frac_size = max(
        numeric_type.fraction_digits_value for numeric_type in numeric_types
    )
    total_size = int_size + int(is_signed) + frac_size
    return RegisterArithmeticInfo(
        size=total_size, is_signed=is_signed, fraction_places=frac_size
    )


def _eval_num(val: ast.AST) -> float:
    if isinstance(val, ast.Num):
        return cast(float, val.value)
    if isinstance(val, ast.UnaryOp) and isinstance(val.op, ast.USub):
        return -_eval_num(val.operand)
    raise ClassiqValueError(
        "Classical lists with quantum subscripts must contain compile-time classical "
        "real numbers"
    )


class _QuantumSubscriptRemover(ast.NodeTransformer):
    def __init__(self, machine_precision: int) -> None:
        self._machine_precision = machine_precision
        self.substitutions_types: dict[str, QuantumNumeric] = {}

    def visit_Call(self, node: ast.Call) -> ast.expr:
        if not isinstance(node.func, ast.Name) or node.func.id != "Piecewise":
            return node
        items = [_eval_num(cast(ast.Tuple, arg).elts[0]) for arg in node.args]
        numeric_types = [
            compute_arithmetic_result_type(str(num), {}, self._machine_precision)
            for num in items
        ]
        unified_numeric_type = register_info_to_quantum_type(
            aggregate_numeric_types(numeric_types)
        )
        substitution_var_name = f"lut__{len(self.substitutions_types)}__"
        self.substitutions_types[substitution_var_name] = unified_numeric_type
        return ast.Name(id=substitution_var_name)


class _NameCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        self.names.add(node.id)


def _substitute_quantum_subscripts(
    expr_str: str, var_types: dict[str, QuantumType], machine_precision: int
) -> tuple[str, dict[str, QuantumType]]:
    """
    Remove quantum lookup expressions ([1, 2, 3, 4][n]) from an arithmetic expression
    for the purpose of calculating its numeric attributes.
    Each quantum lookup expression is replaced by a numeric value with equivalent
    numeric properties.

    Args:
        expr_str: arithmetic expression
        var_types: quantum variable type mapping
        machine_precision: global machine precision

    Returns:
        1. the reduced expression
        2. updated type mapping
    """
    expr_ast = ast.parse(expr_str)
    subscript_remover = _QuantumSubscriptRemover(machine_precision)
    expr_ast = subscript_remover.visit(expr_ast)
    var_types_substituted = var_types | subscript_remover.substitutions_types
    expr_str_substituted = ast.unparse(expr_ast)
    names_collector = _NameCollector()
    names_collector.visit(ast.parse(expr_str_substituted))
    var_types_substituted = {
        var_name: var_type
        for var_name, var_type in var_types_substituted.items()
        if var_name in names_collector.names
    }
    return expr_str_substituted, var_types_substituted
