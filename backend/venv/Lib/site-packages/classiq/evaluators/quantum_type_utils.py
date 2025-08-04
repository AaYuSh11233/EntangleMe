from classiq.interface.exceptions import (
    ClassiqExpansionError,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.inplace_binary_operation import BinaryOperation
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumNumeric,
    QuantumScalar,
    QuantumType,
)

from classiq.model_expansions.scope import QuantumSymbol, Scope


def validate_bind_targets(bind: BindOperation, scope: Scope) -> None:
    illegal_qnum_bind_targets = []
    for out_handle in bind.out_handles:
        out_var = scope[out_handle.name].as_type(QuantumSymbol)
        out_var_type = out_var.quantum_type
        if not isinstance(out_var_type, QuantumNumeric):
            continue
        if not out_var_type.has_size_in_bits:
            illegal_qnum_bind_targets.append(str(out_var.handle))
    if len(illegal_qnum_bind_targets) > 0:
        raise ClassiqExpansionError(
            f"QNum bind targets {illegal_qnum_bind_targets!r} must be declared or initialized with size, sign, and fraction digits"
        )


def get_inplace_op_scalar_as_numeric(
    var: QuantumSymbol, operation: BinaryOperation, var_kind: str
) -> QuantumNumeric:
    if not isinstance(var.quantum_type, QuantumScalar):
        raise ClassiqExpansionError(
            f"Cannot perform inplace {operation.name.lower()} with non-scalar {var_kind} {var.handle}"
        )
    if isinstance(var.quantum_type, QuantumNumeric):
        return var.quantum_type
    if isinstance(var.quantum_type, QuantumBit):
        return QuantumNumeric(
            size=Expression(expr="1"),
            is_signed=Expression(expr="False"),
            fraction_digits=Expression(expr="0"),
        )
    raise ClassiqInternalExpansionError(f"Unexpected scalar type {var.quantum_type}")


def set_bounds(from_type: QuantumType, to_type: QuantumNumeric) -> None:
    if not isinstance(from_type, QuantumNumeric):
        to_type.reset_bounds()
        return

    if from_type.is_evaluated and to_type.is_evaluated:
        same_attributes = to_type.sign_value == from_type.sign_value and (
            to_type.fraction_digits_value == from_type.fraction_digits_value
        )
    else:
        same_attributes = (
            (from_type.is_signed is not None and from_type.fraction_digits is not None)
            and (to_type.is_signed is not None and to_type.fraction_digits is not None)
            and (to_type.is_signed.expr == from_type.is_signed.expr)
            and (to_type.fraction_digits.expr == from_type.fraction_digits.expr)
        )

    if same_attributes:
        to_type.set_bounds(from_type.get_bounds())
    else:
        to_type.reset_bounds()
