import inspect
import sys
from collections.abc import Mapping
from types import FrameType
from typing import (
    Any,
    Callable,
    Final,
    NoReturn,
    Optional,
    Union,
    overload,
)

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.builtins.internal_operators import (
    REPEAT_OPERATOR_NAME,
)
from classiq.interface.generator.functions.classical_type import Integer
from classiq.interface.helpers.text_utils import s
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.bounds import SetBoundsStatement
from classiq.interface.model.classical_if import ClassicalIf
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.control import Control
from classiq.interface.model.invert import Invert
from classiq.interface.model.phase_operation import PhaseOperation
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
    ArithmeticOperationKind,
)
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_lambda_function import QuantumLambdaFunction
from classiq.interface.model.repeat import Repeat
from classiq.interface.model.statement_block import StatementBlock
from classiq.interface.model.within_apply_operation import WithinApply

from classiq.qmod.generative import is_generative_mode
from classiq.qmod.qmod_constant import QConstant
from classiq.qmod.qmod_variable import Input, Output, QArray, QBit, QNum, QScalar, QVar
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.quantum_expandable import prepare_arg
from classiq.qmod.symbolic_expr import SymbolicExpr
from classiq.qmod.utilities import Statements, get_source_ref, suppress_return_value

_MISSING_VALUE: Final[int] = -1


@overload
def allocate(num_qubits: Union[int, SymbolicExpr], out: Output[QVar]) -> None:
    pass


@overload
def allocate(out: Output[QVar]) -> None:
    pass


@overload
def allocate(
    num_qubits: Union[int, SymbolicExpr],
    is_signed: Union[bool, SymbolicExpr],
    fraction_digits: Union[int, SymbolicExpr],
    out: Output[QVar],
) -> None:
    pass


@suppress_return_value
def allocate(*args: Any, **kwargs: Any) -> None:
    """
    Initialize a quantum variable to a new quantum object in the zero state:

    $$
        \\left|\\text{out}\\right\\rangle = \\left|0\\right\\rangle^{\\otimes \\text{num_qubits}}
    $$

    If 'num_qubits' is not specified, it will be inferred according to the type of 'out'.
    In case the quantum variable is of type `QNum`, its numeric attributes can be specified as
    well.

    Args:
        num_qubits: The number of qubits to allocate (positive integer, optional).
        out: The quantum variable that will receive the allocated qubits. Must be uninitialized before allocation.
        is_signed: The sign of the allocated variable, valid only for `QNum` (boolean, optional).
        fraction_digits: The number of fraction digits in the allocated variable, valid only for `QNum` (positive integer, optional).

    Notes:
        1. If the output variable has been declared with a specific number of qubits or numeric attributes, the passed values must match the declared values.
        2. The synthesis engine automatically handles the allocation, either by drawing new qubits from the available pool or by reusing existing ones.
    """
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    if len(args) == 0:
        size = kwargs.get("num_qubits", None)
        is_signed = kwargs.get("is_signed", None)
        fraction_digits = kwargs.get("fraction_digits", None)
        target = kwargs["out"]
    elif len(args) == 1:
        if "out" in kwargs:
            size = args[0]
            is_signed = kwargs.get("is_signed", None)
            fraction_digits = kwargs.get("fraction_digits", None)
            target = kwargs["out"]
        else:
            size = None
            is_signed = None
            fraction_digits = None
            target = args[0]
    elif len(args) == 2:
        size, target = args
        is_signed = kwargs.get("is_signed", None)
        fraction_digits = kwargs.get("fraction_digits", None)
    else:
        size, is_signed, fraction_digits, target = args
    if isinstance(size, QConstant):
        size.add_to_model()
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        Allocate(
            size=None if size is None else Expression(expr=str(size)),
            is_signed=None if is_signed is None else Expression(expr=str(is_signed)),
            fraction_digits=(
                None
                if fraction_digits is None
                else Expression(expr=str(fraction_digits))
            ),
            target=target.get_handle_binding(),
            source_ref=source_ref,
        )
    )


@suppress_return_value
def bind(
    source: Union[Input[QVar], list[Input[QVar]]],
    destination: Union[Output[QVar], list[Output[QVar]]],
) -> None:
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    if not isinstance(source, list):
        source = [source]
    if not isinstance(destination, list):
        destination = [destination]
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        BindOperation(
            in_handles=[src_var.get_handle_binding() for src_var in source],
            out_handles=[dst_var.get_handle_binding() for dst_var in destination],
            source_ref=source_ref,
        )
    )


@suppress_return_value
def if_(
    condition: Union[SymbolicExpr, bool],
    then: Union[QCallable, Callable[[], Statements]],
    else_: Union[QCallable, Callable[[], Statements], int] = _MISSING_VALUE,
) -> None:
    _validate_operand(then)
    if else_ != _MISSING_VALUE:
        _validate_operand(else_)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))

    if_stmt = ClassicalIf(
        condition=Expression(expr=str(condition)),
        then=_operand_to_body(then, "then"),
        else_=_operand_to_body(else_, "else_") if else_ != _MISSING_VALUE else [],  # type: ignore[arg-type]
        source_ref=source_ref,
    )
    if is_generative_mode():
        if_stmt.set_generative_block("then", then)
        if callable(else_):
            if_stmt.set_generative_block("else_", else_)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(if_stmt)


@suppress_return_value
def control(
    ctrl: Union[SymbolicExpr, QBit, QArray[QBit], list[QVar]],
    stmt_block: Union[QCallable, Callable[[], Statements]],
    else_block: Union[QCallable, Callable[[], Statements], None] = None,
) -> None:
    _validate_operand(stmt_block)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    control_stmt = Control(
        expression=Expression(expr=str(ctrl)),
        body=_operand_to_body(stmt_block, "stmt_block"),
        else_block=_operand_to_body(else_block, "else_block") if else_block else None,
        source_ref=source_ref,
    )
    if is_generative_mode():
        control_stmt.set_generative_block("body", stmt_block)
        if else_block is not None:
            control_stmt.set_generative_block("else_block", else_block)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(control_stmt)


@suppress_return_value
def assign(expression: SymbolicExpr, target_var: QScalar) -> None:
    """
    Initialize a scalar quantum variable using an arithmetic expression.
    If specified, the variable numeric properties (size, signedness, and fraction
    digits) must match the expression properties.

    Equivalent to `<target_var> |= <expression>`.

    Args:
        expression: A classical or quantum arithmetic expression
        target_var: An uninitialized scalar quantum variable
    """
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        ArithmeticOperation(
            expression=Expression(expr=str(expression)),
            result_var=target_var.get_handle_binding(),
            operation_kind=ArithmeticOperationKind.Assignment,
            source_ref=source_ref,
        )
    )


@suppress_return_value
def assign_amplitude(expression: SymbolicExpr, target_var: QScalar) -> None:
    """
    Perform an amplitude-encoding assignment operation on a quantum variable and a
    quantum expression.

    Equivalent to `<target_var> *= <expression>`.

    Args:
        expression: A quantum arithmetic expression
        target_var: A scalar quantum variable
    """
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        AmplitudeLoadingOperation(
            expression=Expression(expr=str(expression)),
            result_var=target_var.get_handle_binding(),
            source_ref=source_ref,
        )
    )


@suppress_return_value
def inplace_add(expression: SymbolicExpr, target_var: QScalar) -> None:
    """
    Add an arithmetic expression to a quantum variable.

    Equivalent to `<target_var> += <expression>`.

    Args:
        expression: A classical or quantum arithmetic expression
        target_var: A scalar quantum variable
    """
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        ArithmeticOperation(
            expression=Expression(expr=str(expression)),
            result_var=target_var.get_handle_binding(),
            operation_kind=ArithmeticOperationKind.InplaceAdd,
            source_ref=source_ref,
        )
    )


@suppress_return_value
def inplace_xor(expression: SymbolicExpr, target_var: QScalar) -> None:
    """
    Bitwise-XOR a quantum variable with an arithmetic expression.

    Equivalent to `<target_var> ^= <expression>`.

    Args:
        expression: A classical or quantum arithmetic expression
        target_var: A scalar quantum variable
    """
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        ArithmeticOperation(
            expression=Expression(expr=str(expression)),
            result_var=target_var.get_handle_binding(),
            operation_kind=ArithmeticOperationKind.InplaceXor,
            source_ref=source_ref,
        )
    )


@suppress_return_value
def within_apply(
    within: Callable[[], Statements],
    apply: Callable[[], Statements],
) -> None:
    _validate_operand(within)
    _validate_operand(apply)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    within_apply_stmt = WithinApply(
        compute=_operand_to_body(within, "within"),
        action=_operand_to_body(apply, "apply"),
        source_ref=source_ref,
    )
    if is_generative_mode():
        within_apply_stmt.set_generative_block("within", within)
        within_apply_stmt.set_generative_block("apply", apply)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(within_apply_stmt)


@suppress_return_value
def repeat(
    count: Union[SymbolicExpr, int], iteration: Callable[[int], Statements]
) -> None:
    _validate_operand(iteration, num_params=1)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    iteration_operand = prepare_arg(
        QuantumOperandDeclaration(
            name=REPEAT_OPERATOR_NAME,
            positional_arg_declarations=[
                ClassicalParameterDeclaration(name="index", classical_type=Integer()),
            ],
        ),
        iteration,
        repeat.__name__,
        "iteration",
    )
    if not isinstance(iteration_operand, QuantumLambdaFunction):
        raise ClassiqValueError(
            "Argument 'iteration' to 'repeat' should be a callable that takes one integer argument."
        )

    repeat_stmt = Repeat(
        iter_var=inspect.getfullargspec(iteration).args[0],
        count=Expression(expr=str(count)),
        body=iteration_operand.body,
        source_ref=source_ref,
    )
    if is_generative_mode():
        repeat_stmt.set_generative_block("body", iteration)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(repeat_stmt)


@suppress_return_value
def power(
    exponent: Union[SymbolicExpr, int],
    stmt_block: Union[QCallable, Callable[[], Statements]],
) -> None:
    _validate_operand(stmt_block)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    power_stmt = Power(
        power=Expression(expr=str(exponent)),
        body=_operand_to_body(stmt_block, "stmt_block"),
        source_ref=source_ref,
    )
    if is_generative_mode():
        power_stmt.set_generative_block("body", stmt_block)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(power_stmt)


@suppress_return_value
def invert(stmt_block: Union[QCallable, Callable[[], Statements]]) -> None:
    _validate_operand(stmt_block)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    invert_stmt = Invert(
        body=_operand_to_body(stmt_block, "stmt_block"), source_ref=source_ref
    )
    if is_generative_mode():
        invert_stmt.set_generative_block("body", stmt_block)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(invert_stmt)


@suppress_return_value
def phase(expr: SymbolicExpr, theta: float = 1.0) -> None:
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        PhaseOperation(
            expression=Expression(expr=str(expr)),
            theta=Expression(expr=str(theta)),
            source_ref=source_ref,
        )
    )


@suppress_return_value
def block(
    statements: Union[QCallable, Callable[[], Statements]],
) -> None:
    _validate_operand(statements)
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))

    block_stmt = Block(
        statements=_operand_to_body(statements, "statements"),
        source_ref=source_ref,
    )
    if is_generative_mode():
        block_stmt.set_generative_block("statements", statements)
    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(block_stmt)


@overload
def reset_bounds(
    target_var: QNum,
) -> None:
    pass


@overload
def reset_bounds(
    target_var: QNum,
    lower_bound: Union[float, SymbolicExpr],
    upper_bound: Union[float, SymbolicExpr],
) -> None:
    pass


@suppress_return_value
def reset_bounds(
    target_var: QNum,
    lower_bound: Optional[Union[float, SymbolicExpr]] = None,
    upper_bound: Optional[Union[float, SymbolicExpr]] = None,
) -> None:
    assert QCallable.CURRENT_EXPANDABLE is not None
    source_ref = get_source_ref(sys._getframe(1))

    lower_bound_expr = (
        None if lower_bound is None else Expression(expr=str(lower_bound))
    )
    upper_bound_expr = (
        None if upper_bound is None else Expression(expr=str(upper_bound))
    )

    QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
        SetBoundsStatement(
            target=target_var.get_handle_binding(),
            lower_bound=lower_bound_expr,
            upper_bound=upper_bound_expr,
            source_ref=source_ref,
        )
    )


def _validate_operand(stmt_block: Any, num_params: int = 0) -> None:
    if stmt_block is None:
        _raise_operand_error(
            lambda operation_name, operand_arg_name: (
                f"{operation_name!r} is missing required argument for "
                f"parameter {operand_arg_name!r}"
            ),
            num_params,
        )
    if isinstance(stmt_block, QCallable):
        return
    op_spec = inspect.getfullargspec(stmt_block)
    params = op_spec.args[: len(op_spec.args) - len(op_spec.defaults or ())]
    if len(params) > num_params or (
        len(params) < num_params and op_spec.varargs is None
    ):
        _raise_operand_error(
            lambda operation_name, operand_arg_name: (
                f"{operation_name!r} argument for {operand_arg_name!r} has "
                f"{len(params)} parameter{s(params)} but {num_params} expected"
            ),
            num_params,
        )


def _raise_operand_error(
    error_template: Callable[[str, str], str], num_params: int
) -> NoReturn:
    currentframe: FrameType = inspect.currentframe().f_back  # type: ignore[assignment,union-attr]
    operation_frame: FrameType = currentframe.f_back  # type: ignore[assignment]
    operation_frame_info: inspect.Traceback = inspect.getframeinfo(operation_frame)
    operation_name: str = operation_frame_info.function
    context = operation_frame_info.code_context
    assert context is not None
    operand_arg_name = (
        context[0].split("_validate_operand(")[1].split(")")[0].split(",")[0]
    )
    operation_parameters = inspect.signature(
        operation_frame.f_globals[operation_name]
    ).parameters
    raise ClassiqValueError(
        error_template(operation_name, operand_arg_name)
        + _get_operand_hint(
            operation_name=operation_name,
            operand_arg_name=operand_arg_name,
            params=operation_parameters,
            num_params=num_params,
        )
    )


def _get_operand_hint(
    operation_name: str,
    operand_arg_name: str,
    params: Mapping[str, inspect.Parameter],
    num_params: int,
) -> str:
    if operation_name == "repeat":
        operand_params = " i"
    else:
        operand_params = (
            ""
            if num_params == 0
            else f" {', '.join([f'p{i}' for i in range(num_params)])}"
        )
    args = [
        (
            f"{param.name}=lambda{operand_params}: ..."
            if param.name == operand_arg_name
            else f"{param.name}=..."
        )
        for param in params.values()
    ]
    return f"\nHint: Write '{operation_name}({', '.join(args)})'"


def _operand_to_body(
    callable_: Union[QCallable, Callable[[], Statements]], param_name: str
) -> StatementBlock:
    op_name = sys._getframe(1).f_code.co_name
    if (
        isinstance(callable_, QCallable)
        and len(callable_.func_decl.positional_arg_declarations) > 0
    ):
        raise ClassiqValueError(
            f"Callable argument {callable_.func_decl.name!r} to {op_name!r} should "
            f"not accept arguments."
        )
    to_operand = prepare_arg(
        QuantumOperandDeclaration(name=""), callable_, op_name, param_name
    )
    if isinstance(to_operand, str):
        return [QuantumFunctionCall(function=to_operand)]
    elif isinstance(to_operand, QuantumLambdaFunction):
        return to_operand.body
    else:
        raise ValueError(f"Unexpected operand type: {type(to_operand)}")


__all__ = [
    "allocate",
    "assign",
    "assign_amplitude",
    "bind",
    "block",
    "control",
    "if_",
    "inplace_add",
    "inplace_xor",
    "invert",
    "phase",
    "power",
    "repeat",
    "reset_bounds",
    "within_apply",
]


def __dir__() -> list[str]:
    return __all__
