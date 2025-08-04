import ast
from collections.abc import Mapping, Sequence
from enum import IntEnum
from typing import Any, Callable, Optional, cast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.arith.machine_precision import (
    DEFAULT_MACHINE_PRECISION,
)
from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.types.enum_declaration import EnumDeclaration
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.helpers.pydantic_model_helpers import nameables_to_dict

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.attribute_evaluation import eval_attribute
from classiq.evaluators.qmod_node_evaluators.binary_op_evaluation import eval_binary_op
from classiq.evaluators.qmod_node_evaluators.bool_op_evaluation import eval_bool_op
from classiq.evaluators.qmod_node_evaluators.classical_function_evaluation import (
    eval_function,
    eval_symbolic_function,
    try_eval_builtin_function,
    try_eval_sympy_function,
)
from classiq.evaluators.qmod_node_evaluators.compare_evaluation import eval_compare
from classiq.evaluators.qmod_node_evaluators.constant_evaluation import (
    eval_constant,
    eval_enum_member,
    try_eval_qmod_literal,
    try_eval_sympy_constant,
)
from classiq.evaluators.qmod_node_evaluators.list_evaluation import eval_list
from classiq.evaluators.qmod_node_evaluators.measurement_evaluation import (
    eval_measurement,
)
from classiq.evaluators.qmod_node_evaluators.min_max_evaluation import eval_min_max_op
from classiq.evaluators.qmod_node_evaluators.name_evaluation import eval_name
from classiq.evaluators.qmod_node_evaluators.piecewise_evaluation import eval_piecewise
from classiq.evaluators.qmod_node_evaluators.struct_instantiation_evaluation import (
    eval_struct_instantiation,
)
from classiq.evaluators.qmod_node_evaluators.subscript_evaluation import (
    eval_quantum_subscript,
    eval_subscript,
)
from classiq.evaluators.qmod_node_evaluators.unary_op_evaluation import eval_unary_op
from classiq.evaluators.qmod_node_evaluators.utils import is_classical_type

_SUPPORTED_NODES = (
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.Name,
    ast.List,
    ast.cmpop,
    ast.operator,
    ast.expr_context,
    ast.keyword,
    ast.unaryop,
    ast.boolop,
    ast.Slice,
)


class QmodExpressionEvaluator(ast.NodeVisitor):
    def __init__(
        self,
        expr_val: QmodAnnotatedExpression,
        *,
        treat_qnum_as_float: bool = False,
        machine_precision: int = DEFAULT_MACHINE_PRECISION,
        classical_struct_declarations: Optional[Sequence[StructDeclaration]] = None,
        enum_declarations: Optional[Sequence[EnumDeclaration]] = None,
        classical_function_declarations: Optional[
            Sequence[ClassicalFunctionDeclaration]
        ] = None,
        classical_function_callables: Optional[Mapping[str, Callable]] = None,
        scope: Optional[dict[str, Any]] = None,
    ) -> None:
        self._expr_val = expr_val
        self._treat_qnum_as_float = treat_qnum_as_float
        self._machine_precision = machine_precision
        self._classical_struct_decls = nameables_to_dict(
            classical_struct_declarations or []
        )
        self._enum_declarations = {decl.name: decl for decl in enum_declarations or []}
        self._enums: dict[str, type[IntEnum]] = {}
        self._classical_function_declarations = nameables_to_dict(
            classical_function_declarations or []
        )
        self._classical_function_callables = classical_function_callables or {}
        self._scope = scope or {}

    def visit(self, node: ast.AST) -> None:
        if not isinstance(node, _SUPPORTED_NODES):
            raise ClassiqInternalExpansionError(
                f"Syntax error: {type(node).__name__!r} is not supported"
            )
        super().visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        super().generic_visit(node)
        eval_bool_op(self._expr_val, node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        super().generic_visit(node)
        eval_binary_op(
            self._expr_val, node, self._treat_qnum_as_float, self._machine_precision
        )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        super().generic_visit(node)
        eval_unary_op(self._expr_val, node, self._machine_precision)

    def visit_Compare(self, node: ast.Compare) -> None:
        super().generic_visit(node)
        eval_compare(self._expr_val, node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if not isinstance(func, ast.Name):
            raise ClassiqExpansionError(
                f"Function {ast.unparse(node.func)!r} is not supported"
            )
        func_name = func.id

        if func_name == "Piecewise":
            self._eval_piecewise(node)
            return

        for arg in node.args:
            self.visit(arg)
        for kwarg in node.keywords:
            self.visit(kwarg)

        if func_name == "measure":
            eval_measurement(self._expr_val, node)
            return

        if func_name in ("min", "max"):
            eval_min_max_op(
                self._expr_val,
                node,
                func_name,
                self._treat_qnum_as_float,
                self._machine_precision,
            )
            return

        # FIXME: Remove (CLS-3241)
        if func_name in self._classical_struct_decls:
            eval_struct_instantiation(
                self._expr_val, node, self._classical_struct_decls[func_name]
            )
            return

        # FIXME: Remove (CLS-3241)
        if func_name in self._classical_function_callables:
            if func_name not in self._classical_function_declarations:
                raise ClassiqInternalExpansionError
            eval_function(
                self._expr_val,
                node,
                self._classical_function_declarations[func_name],
                self._classical_function_callables[func_name],
            )
            return

        if func_name in self._classical_function_declarations:
            eval_symbolic_function(
                self._expr_val, node, self._classical_function_declarations[func_name]
            )
            return

        if try_eval_builtin_function(self._expr_val, node, func_name):
            return

        if try_eval_sympy_function(self._expr_val, node, func_name):
            return

        raise ClassiqExpansionError(f"{func.id!r} is undefined")

    def _eval_piecewise(self, node: ast.Call) -> None:
        if (
            len(node.args) == 0
            or len(node.keywords) != 0
            or not all(
                isinstance(arg, ast.Tuple) and len(arg.elts) == 2 for arg in node.args
            )
        ):
            raise ClassiqExpansionError("Malformed Piecewise expression")
        args = [(arg.elts[0], arg.elts[1]) for arg in cast(list[ast.Tuple], node.args)]
        for value, cond in args:
            self.visit(value)
            self.visit(cond)
        eval_piecewise(self._expr_val, node, args)

    def visit_Constant(self, node: ast.Constant) -> None:
        eval_constant(self._expr_val, node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            isinstance(node.value, ast.Name)
            and (enum_name := node.value.id) in self._enum_declarations
        ):
            if enum_name not in self._enums:
                self._enums[enum_name] = self._enum_declarations[
                    enum_name
                ].create_enum()
            eval_enum_member(self._expr_val, node, self._enums[enum_name])
            return
        super().generic_visit(node)
        eval_attribute(self._expr_val, node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        super().generic_visit(node)
        if not isinstance(node.slice, ast.Slice) and not is_classical_type(
            self._expr_val.get_type(node.slice)
        ):
            eval_quantum_subscript(self._expr_val, node, self._machine_precision)
            return
        eval_subscript(self._expr_val, node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self._scope:
            eval_name(self._expr_val, node, self._scope[node.id])
            return
        if try_eval_sympy_constant(self._expr_val, node):
            return
        if try_eval_qmod_literal(self._expr_val, node):
            return

        raise ClassiqExpansionError(f"Variable {node.id!r} is undefined")

    def visit_List(self, node: ast.List) -> None:
        super().generic_visit(node)
        eval_list(self._expr_val, node)


def evaluate_qmod_expression(
    expr: str,
    *,
    treat_qnum_as_float: bool = False,
    machine_precision: int = DEFAULT_MACHINE_PRECISION,
    classical_struct_declarations: Optional[Sequence[StructDeclaration]] = None,
    enum_declarations: Optional[Sequence[EnumDeclaration]] = None,
    classical_function_declarations: Optional[
        Sequence[ClassicalFunctionDeclaration]
    ] = None,
    classical_function_callables: Optional[Mapping[str, Callable]] = None,
    scope: Optional[dict[str, Any]] = None,
) -> QmodAnnotatedExpression:
    expr_ast = ast.parse(expr, mode="eval").body
    expr_value = QmodAnnotatedExpression(expr_ast)
    QmodExpressionEvaluator(
        expr_value,
        treat_qnum_as_float=treat_qnum_as_float,
        machine_precision=machine_precision,
        classical_struct_declarations=classical_struct_declarations,
        enum_declarations=enum_declarations,
        classical_function_declarations=classical_function_declarations,
        classical_function_callables=classical_function_callables,
        scope=scope,
    ).visit(expr_value.root)
    return expr_value
