from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.arith.arithmetic import is_bool
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
    ArithmeticOperationKind,
)
from classiq.interface.model.quantum_type import QuantumBit, QuantumNumeric

from classiq.model_expansions.scope import QuantumSymbol


def validate_assignment_bool_expression(
    result_symbol: QuantumSymbol, expr: str, op_kind: ArithmeticOperationKind
) -> None:
    if not is_bool(expr):
        return
    _validate_target_type(result_symbol, expr, op_kind)


def _validate_target_type(
    target_symbol: QuantumSymbol, expr: str, op_kind: ArithmeticOperationKind
) -> None:
    supported_types = _supported_types()
    if target_symbol.quantum_type.qmod_type_name not in supported_types:
        raise ClassiqValueError(
            f'The expression has been evaluated to "{expr}" which is a Boolean value. '
            f"Cannot perform {op_kind.value} operation of Boolean expression to result variable '{target_symbol.handle}' of type {target_symbol.quantum_type.qmod_type_name}. "
            f"Boolean expressions can only be applied on {' or '.join(supported_types)}."
        )


def convert_assignment_bool_expression(op: ArithmeticOperation) -> None:
    if not is_bool(op.expression.expr):
        return
    op.expression = op.expression.model_copy(
        update=dict(expr="1" if op.expression.expr == "True" else "0")
    )


def convert_inplace_op_bool_expression(
    op: ArithmeticOperation, target: QuantumSymbol
) -> None:
    if not is_bool(op.expression.expr):
        return
    _validate_target_type(target, op.expression.expr, op.operation_kind)
    op.expression = Expression(expr="1" if op.expression.expr == "True" else "0")


def _supported_types() -> tuple[str, ...]:
    return (
        QuantumBit().qmod_type_name,
        QuantumNumeric(
            size=Expression(expr="1"),
            is_signed=Expression(expr="False"),
            fraction_digits=Expression(expr="0"),
        ).qmod_type_name,
    )
