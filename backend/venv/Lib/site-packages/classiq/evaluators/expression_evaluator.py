import ast
from collections.abc import Mapping
from enum import EnumMeta
from typing import Any

from sympy import SympifyError, sympify

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.constant import Constant
from classiq.interface.generator.expressions.evaluated_expression import (
    EvaluatedExpression,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.expression_types import ExpressionValue
from classiq.interface.generator.expressions.non_symbolic_expr import NonSymbolicExpr
from classiq.interface.generator.expressions.proxies.quantum.qmod_sized_proxy import (
    QmodSizedProxy,
)
from classiq.interface.generator.expressions.sympy_supported_expressions import (
    SYMPY_SUPPORTED_EXPRESSIONS,
)

from classiq.model_expansions.atomic_expression_functions_defs import (
    ATOMIC_EXPRESSION_FUNCTIONS,
    qmod_val_to_python,
)
from classiq.model_expansions.sympy_conversion.expression_to_sympy import (
    translate_to_sympy,
)
from classiq.model_expansions.sympy_conversion.sympy_to_python import sympy_to_python
from classiq.qmod import symbolic
from classiq.qmod.builtins.enums import BUILTIN_ENUM_DECLARATIONS
from classiq.qmod.model_state_container import QMODULE


def evaluate_constants(constants: list[Constant]) -> dict[str, EvaluatedExpression]:
    result: dict[str, EvaluatedExpression] = {}
    for constant in constants:
        result[constant.name] = evaluate(constant.value, result)
    return result


def evaluate_constants_as_python(constants: list[Constant]) -> dict[str, Any]:
    evaluated = evaluate_constants(constants)
    return {
        constant.name: qmod_val_to_python(
            evaluated[constant.name].value, constant.const_type
        )
        for constant in constants
    }


def _quick_eval(expr: str) -> Any:
    try:
        return int(expr)
    except ValueError:
        pass
    try:
        return float(expr)
    except ValueError:
        pass
    return None


def evaluate(
    expr: Expression, locals_dict: Mapping[str, EvaluatedExpression]
) -> EvaluatedExpression:
    val = _quick_eval(expr.expr)
    if val is not None:
        return EvaluatedExpression(value=val)

    model_locals: dict[str, ExpressionValue] = {}
    model_locals.update(ATOMIC_EXPRESSION_FUNCTIONS)
    model_locals.update(
        {
            enum_decl.name: enum_decl.create_enum()
            for enum_decl in (QMODULE.enum_decls | BUILTIN_ENUM_DECLARATIONS).values()
        }
    )
    # locals override builtin-functions
    model_locals.update({name: expr.value for name, expr in locals_dict.items()})

    _validate_undefined_vars(expr.expr, model_locals)

    sympy_expr = translate_to_sympy(expr.expr)
    try:
        sympify_result = sympify(sympy_expr, locals=model_locals)
    except (TypeError, IndexError) as e:
        raise ClassiqExpansionError(str(e)) from e
    except AttributeError as e:
        if isinstance(e.obj, EnumMeta):
            raise ClassiqExpansionError(
                f"Enum {e.obj.__name__} has no member {e.name!r}. Available members: "
                f"{', '.join(e.obj.__members__)}"
            ) from e
        raise
    except SympifyError as e:
        expr = e.expr
        if isinstance(expr, QmodSizedProxy) and isinstance(expr, NonSymbolicExpr):
            raise ClassiqExpansionError(
                f"{expr.type_name} {str(expr)!r} does not support arithmetic operations"
            ) from e
        raise

    return EvaluatedExpression(
        value=sympy_to_python(sympify_result, locals=model_locals)
    )


def _validate_undefined_vars(
    expr: str, model_locals: dict[str, ExpressionValue]
) -> None:
    id_visitor = _VarsCollector()
    id_visitor.visit(ast.parse(expr))
    identifiers = id_visitor.vars
    undefined_vars = (
        identifiers
        - model_locals.keys()
        - set(SYMPY_SUPPORTED_EXPRESSIONS)
        - set(symbolic.__all__)
    )

    if len(undefined_vars) == 1:
        undefined_var = undefined_vars.__iter__().__next__()
        raise ClassiqExpansionError(f"Variable {undefined_var!r} is undefined")
    elif len(undefined_vars) > 1:
        raise ClassiqExpansionError(f"Variables {list(undefined_vars)} are undefined")


class _VarsCollector(ast.NodeTransformer):
    def __init__(self) -> None:
        self.vars: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        self.vars.add(node.id)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        self.visit(func)
        if not isinstance(func, ast.Name) or func.id != "struct_literal":
            for arg in node.args:
                self.visit(arg)
        for kw in node.keywords:
            self.visit(kw)
