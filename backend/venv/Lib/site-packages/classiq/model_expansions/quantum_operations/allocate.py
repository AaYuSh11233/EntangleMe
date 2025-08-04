from typing import TYPE_CHECKING, Union

import sympy

from classiq.interface.debug_info.debug_info import FunctionDebugInfo
from classiq.interface.exceptions import ClassiqExpansionError, ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.handle_binding import NestedHandleBinding
from classiq.interface.model.quantum_type import (
    QuantumBitvector,
    QuantumNumeric,
)

from classiq.evaluators.qmod_type_inference.quantum_type_inference import (
    inject_quantum_type_attributes_inplace,
)
from classiq.model_expansions.quantum_operations.emitter import Emitter
from classiq.model_expansions.scope import QuantumSymbol

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class AllocateEmitter(Emitter[Allocate]):
    def __init__(
        self, interpreter: "BaseInterpreter", allow_symbolic_attrs: bool = False
    ) -> None:
        super().__init__(interpreter)
        self._allow_symbolic_attrs = allow_symbolic_attrs

    def emit(self, allocate: Allocate, /) -> bool:
        target: QuantumSymbol = self._interpreter.evaluate(allocate.target).as_type(
            QuantumSymbol
        )

        if isinstance(target.handle, NestedHandleBinding):
            raise ClassiqValueError(
                f"Cannot allocate partial quantum variable {str(target.handle)!r}"
            )

        op_update_dict: dict[str, Expression] = {}

        if allocate.size is None:
            if allocate.is_signed is not None or allocate.fraction_digits is not None:
                raise ClassiqValueError(
                    "Numeric attributes cannot be specified without size"
                )
            self._handle_without_size(target, op_update_dict)

        elif allocate.is_signed is None and allocate.fraction_digits is None:
            self._handle_with_size(target, allocate.size, op_update_dict)

        elif allocate.is_signed is not None and allocate.fraction_digits is not None:
            self._handle_with_numeric_attrs(
                target,
                allocate.size,
                allocate.is_signed,
                allocate.fraction_digits,
                op_update_dict,
            )

        else:
            raise ClassiqValueError(
                "Sign and fraction digits must be specified together"
            )

        if isinstance(target.quantum_type, QuantumNumeric):
            target.quantum_type.set_bounds((0, 0))

        allocate = allocate.model_copy(update=op_update_dict)
        self._register_debug_info(allocate)
        self.emit_statement(allocate)
        return True

    def _handle_without_size(
        self,
        target: QuantumSymbol,
        op_update_dict: dict[str, Expression],
    ) -> None:
        if target.quantum_type.is_evaluated:
            expr = str(target.quantum_type.size_in_bits)
        elif self._allow_symbolic_attrs:
            expr = f"{target.handle}.size"
        else:
            raise ClassiqValueError(
                f"Could not infer the size of variable {str(target.handle)!r}"
            )
        op_update_dict["size"] = Expression(expr=expr)

    def _handle_with_size(
        self,
        target: QuantumSymbol,
        size: Expression,
        op_update_dict: dict[str, Expression],
    ) -> None:
        size_value = self._interpret_size(size, str(target.handle))
        op_update_dict["size"] = Expression(expr=str(size_value))

        if not isinstance(
            size_value, sympy.Basic
        ) and not inject_quantum_type_attributes_inplace(
            QuantumBitvector(length=op_update_dict["size"]), target.quantum_type
        ):
            raise ClassiqExpansionError(
                f"Cannot allocate {op_update_dict['size']} qubits for variable "
                f"{str(target)!r} of type {target.quantum_type.qmod_type_name}"
            )

    def _handle_with_numeric_attrs(
        self,
        target: QuantumSymbol,
        size: Expression,
        is_signed: Expression,
        fraction_digits: Expression,
        op_update_dict: dict[str, Expression],
    ) -> None:
        var_name = str(target.handle)
        if not isinstance(target.quantum_type, QuantumNumeric):
            raise ClassiqValueError(
                f"Non-numeric variable {var_name!r} cannot be allocated with numeric attributes"
            )

        size_value = self._interpret_size(size, var_name)
        op_update_dict["size"] = Expression(expr=str(size_value))
        is_signed_value = self._interpret_is_signed(is_signed)
        op_update_dict["is_signed"] = Expression(expr=str(is_signed_value))
        fraction_digits_value = self._interpret_fraction_digits(fraction_digits)
        op_update_dict["fraction_digits"] = Expression(expr=str(fraction_digits_value))

        if not (
            isinstance(size_value, sympy.Basic)
            or isinstance(is_signed_value, sympy.Basic)
            or isinstance(fraction_digits_value, sympy.Basic)
        ) and not inject_quantum_type_attributes_inplace(
            QuantumNumeric(
                size=op_update_dict["size"],
                is_signed=op_update_dict["is_signed"],
                fraction_digits=op_update_dict["fraction_digits"],
            ),
            target.quantum_type,
        ):
            raise ClassiqExpansionError(
                f"Cannot allocate {op_update_dict['size']} qubits for variable "
                f"{var_name!r} of type {target.quantum_type.qmod_type_name}"
            )

    def _interpret_size(
        self, size: Expression, var_name: str
    ) -> Union[int, float, sympy.Basic]:
        size_value = self._interpreter.evaluate(size).value
        if not self._allow_symbolic_attrs and not isinstance(size_value, (int, float)):
            if size.expr == f"{var_name}.size":
                raise ClassiqValueError(
                    f"Could not infer the size of variable {var_name!r}"
                )
            raise ClassiqValueError(
                f"The number of allocated qubits must be an integer. Got "
                f"{str(size_value)!r}"
            )
        return size_value

    def _interpret_is_signed(self, is_signed: Expression) -> Union[bool, sympy.Basic]:
        is_signed_value = self._interpreter.evaluate(is_signed).value
        if not self._allow_symbolic_attrs and not isinstance(is_signed_value, bool):
            raise ClassiqValueError(
                f"The sign of a variable must be boolean. Got "
                f"{str(is_signed_value)!r}"
            )
        return is_signed_value

    def _interpret_fraction_digits(
        self, fraction_digits: Expression
    ) -> Union[int, float, sympy.Basic]:
        fraction_digits_value = self._interpreter.evaluate(fraction_digits).value
        if not self._allow_symbolic_attrs and not isinstance(
            fraction_digits_value, (int, float)
        ):
            raise ClassiqValueError(
                f"The fraction digits of a variable must be an integer. Got "
                f"{str(fraction_digits_value)!r}"
            )
        return fraction_digits_value

    def _register_debug_info(self, allocate: Allocate) -> None:
        if (
            allocate.uuid in self._debug_info
            and self._debug_info[allocate.uuid].name != ""
        ):
            return
        parameters: dict[str, str] = {}
        if allocate.size is not None:
            parameters["num_qubits"] = allocate.size.expr
        self._debug_info[allocate.uuid] = FunctionDebugInfo(
            name="allocate",
            port_to_passed_variable_map={"ARG": str(allocate.target)},
            node=allocate._as_back_ref(),
        )
