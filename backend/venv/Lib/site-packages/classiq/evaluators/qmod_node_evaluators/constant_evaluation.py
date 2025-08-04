import ast
from enum import IntEnum
from typing import Any

import sympy

from classiq.interface.exceptions import (
    ClassiqExpansionError,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalType,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import Enum

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import SYMPY_SYMBOLS, QmodType

QMOD_LITERALS: dict[str, tuple[ClassicalType, Any]] = {
    "false": (Bool(), False),
    "true": (Bool(), True),
}


def eval_enum_member(
    expr_val: QmodAnnotatedExpression, node: ast.Attribute, enum: type[IntEnum]
) -> None:
    enum_name = enum.__name__
    enum_members = {  # type: ignore[var-annotated]
        member.name: member for member in list(enum)
    }
    attr = node.attr
    if attr not in enum_members:
        raise ClassiqExpansionError(f"Enum {enum_name} has no member named {attr!r}")

    expr_val.set_type(node, Enum(name=enum_name))
    expr_val.set_value(node, enum_members[attr])


def eval_constant(expr_val: QmodAnnotatedExpression, node: ast.Constant) -> None:
    value = node.value
    expr_val.set_value(node, value)
    constant_type: QmodType
    if isinstance(value, bool):
        constant_type = Bool()
    elif isinstance(value, int):
        constant_type = Integer()
    elif isinstance(value, (float, complex)):
        constant_type = Real()
    else:
        raise ClassiqExpansionError(f"Unsupported constant {str(value)!r}")
    expr_val.set_type(node, constant_type)


def try_eval_qmod_literal(expr_val: QmodAnnotatedExpression, node: ast.Name) -> bool:
    if node.id not in QMOD_LITERALS:
        return False
    lit_type, lit_val = QMOD_LITERALS[node.id]
    expr_val.set_type(node, lit_type)
    expr_val.set_value(node, lit_val)
    return True


def try_eval_sympy_constant(expr_val: QmodAnnotatedExpression, node: ast.Name) -> bool:
    sympy_val = SYMPY_SYMBOLS.get(node.id)
    if not isinstance(sympy_val, sympy.Expr) or not sympy_val.is_constant():
        return False
    constant_type: QmodType
    constant_value: Any
    if sympy_val.is_Integer:
        constant_type = Integer()
        constant_value = int(sympy_val)
    elif sympy_val.is_Boolean:
        constant_type = Bool()
        constant_value = bool(sympy_val)
    elif sympy_val.is_imaginary:
        constant_type = Real()
        constant_value = complex(sympy_val)
    else:
        constant_type = Real()
        constant_value = float(sympy_val)
    expr_val.set_type(node, constant_type)
    expr_val.set_value(node, constant_value)
    return True
