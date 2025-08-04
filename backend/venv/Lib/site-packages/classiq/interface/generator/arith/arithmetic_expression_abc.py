import abc
import ast
import re
from typing import Any, Optional, Union

import networkx as nx
import pydantic
from pydantic import TypeAdapter
from typing_extensions import TypeAlias

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith import number_utils
from classiq.interface.generator.arith.arithmetic_expression_parser import (
    parse_expression,
)
from classiq.interface.generator.arith.arithmetic_expression_validator import (
    validate_expression,
)
from classiq.interface.generator.arith.arithmetic_result_builder import (
    validate_arithmetic_result_type,
)
from classiq.interface.generator.arith.machine_precision import (
    DEFAULT_MACHINE_PRECISION,
)
from classiq.interface.generator.arith.register_user_input import RegisterArithmeticInfo
from classiq.interface.generator.arith.uncomputation_methods import UncomputationMethods
from classiq.interface.generator.expressions.expression_constants import (
    FORBIDDEN_LITERALS,
    SUPPORTED_FUNC_NAMES,
    SUPPORTED_VAR_NAMES_REG,
)
from classiq.interface.generator.function_params import FunctionParams
from classiq.interface.helpers.custom_pydantic_types import PydanticExpressionStr

ValidDefinitions: TypeAlias = Union[
    pydantic.StrictInt, pydantic.StrictFloat, RegisterArithmeticInfo
]


class ArithmeticExpressionABC(abc.ABC, FunctionParams):
    uncomputation_method: UncomputationMethods = UncomputationMethods.optimized
    machine_precision: pydantic.NonNegativeInt = DEFAULT_MACHINE_PRECISION
    expression: PydanticExpressionStr
    definitions: dict[str, ValidDefinitions]
    qubit_count: Optional[pydantic.NonNegativeInt] = None

    def _get_literal_set(self) -> set[str]:
        return _extract_literals(self.expression)

    @classmethod
    def _validate_expression_literals_and_definitions(
        cls, definitions: dict[str, ValidDefinitions], expression: PydanticExpressionStr
    ) -> dict[str, ValidDefinitions]:
        literals = _extract_literals(expression)

        forbidden = literals.intersection(FORBIDDEN_LITERALS)
        if forbidden:
            raise ClassiqValueError(f"The following names are forbidden: {forbidden}")

        defined = set(definitions.keys())
        unused = defined.difference(literals)
        if unused:
            raise ClassiqValueError(f"The following registers are unused: {unused}")

        undefined = literals.difference(defined)
        if undefined:
            raise ClassiqValueError(f"The following names are undefined: {undefined}")
        return definitions

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate_expression(cls, values: Any) -> dict[str, Any]:
        if not isinstance(values, dict):
            return values
        expression_adapter: TypeAdapter = TypeAdapter(Optional[PydanticExpressionStr])
        expression = expression_adapter.validate_python(values.get("expression"))
        definitions_adapter: TypeAdapter = TypeAdapter(
            Optional[dict[str, ValidDefinitions]]
        )
        definition_dict = values.get("definitions")
        if (
            isinstance(definition_dict, list)
            and len(definition_dict) > 0
            and isinstance(definition_dict[0], tuple)
        ):
            definition_dict = dict(definition_dict)
        definitions = definitions_adapter.validate_python(definition_dict)
        machine_precision: Optional[int] = values.get(
            "machine_precision", DEFAULT_MACHINE_PRECISION
        )
        if (
            expression is None
            or expression == ""
            or definitions is None
            or machine_precision is None
        ):
            return values

        try:
            ast_obj = validate_expression(expression, mode="eval")
        except SyntaxError:
            raise ClassiqValueError(
                f"Failed to parse expression {expression!r}"
            ) from None
        cls._validate_ast_obj(ast_obj)

        graph = parse_expression(expression)
        try:
            cls._validate_expression_graph(graph, values)
        except ClassiqValueError as e:
            # This flow was created specifically for inplace Boolean XOR operations like q1 ^ q2.
            # We can't plug equality in previous stages due to SymPy restrictions.
            # Note that we don't validate that the expression itself is Boolean (passing non-Boolean expressions
            # as inplace is currently not supported, so it's a bug).
            if not e.raw_message == "Expression does not support target assignment":
                raise
            ast_parsed_expression = ast.parse(expression)
            ast_expr = ast_parsed_expression.body[0]
            if (
                not isinstance(ast_expr, ast.Expr)
                or not isinstance(ast_expr.value, ast.BinOp)
                or not isinstance(ast_expr.value.op, ast.BitXor)
            ):
                raise
            expression = f"({expression}) == 1"
            graph = parse_expression(expression)
            cls._validate_expression_graph(graph, values)

        validated_defs = cls._validate_expression_literals_and_definitions(
            definitions, expression
        )

        validate_arithmetic_result_type(
            graph=graph,
            definitions=validated_defs,
            machine_precision=machine_precision,
        )

        new_expr, new_defs = cls._replace_const_definitions_in_expression(
            expression, validated_defs, machine_precision
        )
        values["expression"] = new_expr
        values["definitions"] = new_defs
        return values

    @staticmethod
    def _validate_ast_obj(ast_obj: ast.AST) -> None:
        pass

    @staticmethod
    def _validate_expression_graph(graph: nx.DiGraph, values: dict[str, Any]) -> None:
        pass

    @classmethod
    def _replace_const_definitions_in_expression(
        cls,
        expression: str,
        definitions: dict[str, ValidDefinitions],
        machine_precision: int,
    ) -> tuple[str, dict[str, RegisterArithmeticInfo]]:
        new_definitions = dict()
        for var_name, value in definitions.items():
            if isinstance(value, RegisterArithmeticInfo):
                new_definitions[var_name] = value
            elif isinstance(value, (int, float)):
                expression = cls._replace_numeric_value_in_expression(
                    expression, var_name, value, machine_precision
                )
            else:
                raise ClassiqValueError(f"{type(value)} type ({var_name}) is illegal")

        return expression, new_definitions

    @staticmethod
    def _replace_numeric_value_in_expression(
        expression: str, var: str, value: Union[int, float], machine_precision: int
    ) -> str:
        if isinstance(value, float):
            value = number_utils.limit_fraction_places(
                value, machine_precision=machine_precision
            )
        return re.sub(r"\b" + var + r"\b", str(value), expression)


def _extract_literals(expression: str) -> set[str]:
    return set(re.findall(SUPPORTED_VAR_NAMES_REG, expression)) - SUPPORTED_FUNC_NAMES
