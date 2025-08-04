import ast
from typing import Any, Callable, Optional, Union, cast

import sympy

from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.classical_function_declaration import (
    ClassicalFunctionDeclaration,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
    Integer,
    Real,
)
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.helpers.backward_compatibility import zip_strict
from classiq.interface.helpers.pydantic_model_helpers import nameables_to_dict

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import (
    SYMPY_SYMBOLS,
    QmodType,
    array_len,
    element_types,
    is_classical_integer,
)

# These sympy functions are not declared as int funcs for some reason...
INTEGER_FUNCTION_OVERRIDE = {"floor", "ceiling"}


def _check_classical_array_arg_type(
    param_type: Union[ClassicalArray, ClassicalTuple], arg_type: ClassicalType
) -> bool:
    if not isinstance(arg_type, (ClassicalArray, ClassicalTuple)):
        return False
    param_len = array_len(param_type)
    arg_len = array_len(arg_type)
    if param_len is not None and arg_len is not None and param_len != arg_len:
        return False
    if isinstance(param_type, ClassicalArray):
        if isinstance(arg_type, ClassicalArray):
            return check_classical_arg_type(
                param_type.element_type, arg_type.element_type
            )
        return all(
            check_classical_arg_type(param_type.element_type, arg_element_type)
            for arg_element_type in arg_type.element_types
        )
    if isinstance(arg_type, ClassicalArray):
        return all(
            check_classical_arg_type(param_element_type, arg_type.element_type)
            for param_element_type in param_type.element_types
        )
    return all(
        check_classical_arg_type(param_element_type, arg_element_type)
        for param_element_type, arg_element_type in zip_strict(
            param_type.element_types, arg_type.element_types, strict=True
        )
    )


def check_classical_arg_type(
    param_type: ClassicalType, arg_type: ClassicalType
) -> bool:
    if isinstance(param_type, (Integer, Real)):
        return isinstance(arg_type, (Integer, Real))
    if isinstance(param_type, Bool):
        return isinstance(arg_type, Bool)
    if isinstance(param_type, (ClassicalArray, ClassicalTuple)):
        return _check_classical_array_arg_type(param_type, arg_type)
    if not isinstance(param_type, TypeName):
        raise ClassiqInternalExpansionError
    if not isinstance(arg_type, TypeName):
        return False
    if param_type.is_enum or param_type.has_classical_struct_decl:
        return arg_type.name == param_type.name
    raise ClassiqInternalExpansionError


def _check_classical_arg(
    func_name: str, param_name: str, param_type: ClassicalType, arg_type: QmodType
) -> None:
    if not isinstance(arg_type, ClassicalType) or not check_classical_arg_type(
        param_type, arg_type
    ):
        raise ClassiqExpansionError(
            f"Parameter {param_name!r} of function {func_name!r} expects a "
            f"{param_type.qmod_type_name} argument, but got a "
            f"{arg_type.qmod_type_name}"
        )


def check_classical_func_call(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    decl: ClassicalFunctionDeclaration,
) -> None:
    expected_num_args = len(decl.param_decls)
    actual_num_args = len(node.args) + len(node.keywords)
    if expected_num_args != actual_num_args:
        raise ClassiqExpansionError(
            f"Function {decl.name!r} takes {expected_num_args} arguments but "
            f"{actual_num_args} were given"
        )
    params = list(decl.param_decls)
    assigned_params: set[str] = set()
    for arg in node.args:
        param = params.pop(0)
        assigned_params.add(param.name)
        _check_classical_arg(
            decl.name, param.name, param.classical_type, expr_val.get_type(arg)
        )
    remaining_params = nameables_to_dict(params)
    for kwarg in node.keywords:
        if kwarg.arg is None:
            raise ClassiqExpansionError("Star argument syntax is not supported")
        if kwarg.arg not in remaining_params:
            if kwarg.arg in assigned_params:
                raise ClassiqExpansionError(
                    f"Function {decl.name!r} got multiple values for parameter "
                    f"{kwarg.arg!r}"
                )
            raise ClassiqExpansionError(
                f"Function {decl.name!r} has no parameter named {kwarg.arg}"
            )
        assigned_params.add(kwarg.arg)
        param = remaining_params.pop(kwarg.arg)
        _check_classical_arg(
            decl.name, param.name, param.classical_type, expr_val.get_type(kwarg.value)
        )


def eval_symbolic_function(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    decl: ClassicalFunctionDeclaration,
) -> None:
    check_classical_func_call(expr_val, node, decl)
    if decl.return_type is None:
        raise ClassiqInternalExpansionError
    expr_val.set_type(node, decl.return_type)


def eval_function(
    expr_val: QmodAnnotatedExpression,
    node: ast.Call,
    decl: ClassicalFunctionDeclaration,
    func: Callable,
) -> None:
    eval_symbolic_function(expr_val, node, decl)

    args = node.args
    kwargs = {kwarg.arg: kwarg.value for kwarg in node.keywords}
    if None in kwargs:
        raise ClassiqInternalExpansionError
    if not all(expr_val.has_value(arg) for arg in args) or not all(
        expr_val.has_value(kwarg) for kwarg in kwargs.values()
    ):
        return
    arg_values = [expr_val.get_value(arg) for arg in args]
    kwarg_values = {
        cast(str, kwarg_name): expr_val.get_value(kwarg_value)
        for kwarg_name, kwarg_value in kwargs.items()
    }
    expr_val.set_value(node, func(*arg_values, **kwarg_values))


def try_eval_sympy_function(
    expr_val: QmodAnnotatedExpression, node: ast.Call, func_name: str
) -> bool:
    sympy_func = SYMPY_SYMBOLS.get(func_name)
    if not isinstance(sympy_func, sympy.FunctionClass):
        return False
    _validate_no_kwargs(node)
    args: Optional[list[Any]] = None
    sympy_ret_val: Any = None
    if all(expr_val.has_value(arg) for arg in node.args):
        args = [expr_val.get_value(arg) for arg in node.args]
        sympy_ret_val = sympy_func(*args)
        if not isinstance(sympy_ret_val, sympy.Expr):
            raise ClassiqInternalExpansionError
    ret_type: QmodType
    ret_val: Any = None
    if hasattr(sympy_func, "is_Boolean") and sympy_func.is_Boolean:
        ret_type = Bool()
        if args is not None:
            ret_val = bool(sympy_ret_val)
    elif (
        hasattr(sympy_func, "is_Integer") and sympy_func.is_Integer
    ) or func_name in INTEGER_FUNCTION_OVERRIDE:
        ret_type = Integer()
        if args is not None:
            ret_val = int(sympy_ret_val)
    else:
        ret_type = Real()
        if sympy_ret_val is not None:
            if sympy_ret_val.is_imaginary:
                ret_val = complex(sympy_ret_val)
            elif sympy_ret_val.is_real:
                ret_val = float(sympy_ret_val)
            else:
                raise ClassiqInternalExpansionError
    expr_val.set_type(node, ret_type)
    if ret_val is not None:
        expr_val.set_value(node, ret_val)
    return True


def try_eval_builtin_function(
    expr_val: QmodAnnotatedExpression, node: ast.Call, func_name: str
) -> bool:
    args_are_int = all(isinstance(expr_val.get_type(arg), Integer) for arg in node.args)
    args_are_real = all(
        isinstance(expr_val.get_type(arg), (Integer, Real)) for arg in node.args
    )
    arg_is_int_list = (
        len(node.args) == 1
        and isinstance(
            arg_type := expr_val.get_type(node.args[0]),
            (ClassicalArray, ClassicalTuple),
        )
        and all(
            isinstance(element_type, Integer)
            for element_type in element_types(arg_type)
        )
    )
    arg_is_real_list = (
        len(node.args) == 1
        and isinstance(
            arg_type := expr_val.get_type(node.args[0]),
            (ClassicalArray, ClassicalTuple),
        )
        and all(
            isinstance(element_type, (Integer, Real))
            for element_type in element_types(arg_type)
        )
    )
    args_have_values = all(expr_val.has_value(arg) for arg in node.args)

    if func_name == "mod_inverse":
        _validate_no_kwargs(node)
        ret_type: QmodType
        if args_are_int:
            ret_type = Integer()
        elif args_are_real:
            ret_type = Real()
        else:
            raise ClassiqExpansionError(
                "Function 'mod_inverse' expects numeric arguments"
            )
        expr_val.set_type(node, ret_type)
        if args_have_values:
            sympy_val = sympy.mod_inverse(
                *[expr_val.get_value(arg) for arg in node.args]
            )
            ret_val: Any
            if args_are_int:
                ret_val = int(sympy_val)
            elif isinstance(sympy_val, sympy.Expr) and sympy_val.is_imaginary:
                ret_val = complex(sympy_val)
            else:
                ret_val = float(sympy_val)
            expr_val.set_value(node, ret_val)
        return True

    if func_name == "sum":
        _validate_no_kwargs(node)
        if arg_is_int_list:
            ret_type = Integer()
        elif arg_is_real_list:
            ret_type = Real()
        else:
            raise ClassiqExpansionError("Function 'sum' expects numeric arguments")
        expr_val.set_type(node, ret_type)
        if args_have_values:
            expr_val.set_value(node, sum(expr_val.get_value(node.args[0])))
        return True

    if func_name == "sqrt":
        _validate_no_kwargs(node)
        expr_val.set_type(node, Real())
        if args_have_values:
            expr_val.set_value(
                node, sympy.sqrt(*[expr_val.get_value(arg) for arg in node.args])
            )
        return True

    if func_name == "abs":
        _validate_no_kwargs(node)
        if len(node.args) > 0 and is_classical_integer(expr_val.get_type(node.args[0])):
            ret_type = Integer()
        else:
            ret_type = Real()
        expr_val.set_type(node, ret_type)
        if args_have_values:
            expr_val.set_value(
                node, sympy.Abs(*[expr_val.get_value(arg) for arg in node.args])
            )
        return True

    return False


def _validate_no_kwargs(node: ast.Call) -> None:
    if not isinstance(node.func, ast.Name):
        raise ClassiqInternalExpansionError
    if len(node.keywords) > 0:
        raise ClassiqExpansionError(
            f"Keyword argument syntax is not supported for built-in function "
            f"{node.func.id!r}"
        )
