import ast
import functools
import itertools
import warnings
from collections.abc import Collection, Iterator, Sequence
from contextlib import contextmanager
from typing import Optional, Union

from classiq.interface.exceptions import (
    ClassiqDeprecationWarning,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.control import Control
from classiq.interface.model.invert import Invert
from classiq.interface.model.model_visitor import ModelVisitor
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.phase_operation import PhaseOperation
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
)
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumExpressionOperation,
)
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.within_apply_operation import WithinApply
from classiq.interface.source_reference import SourceReference

from classiq.model_expansions.visitors.variable_references import VarRefCollector


def _inconsistent_type_modifier_error(
    port_name: str,
    expected: TypeModifier,
    actual: TypeModifier,
    source_ref: Optional[Union[SourceReference, str]] = None,
) -> str:
    source_ref_str = f"\n\tat {source_ref}" if source_ref else ""
    return (
        f"The use of variable '{port_name}' does not conform to its declared modifier: "
        f"expected '{expected.name}', but found '{actual.name}'.\n"
        f"Tip: If the cumulative use of the variable in the function matches '{expected.name}', "
        f"use the `unchecked` flag to instruct the compiler to disregard individual operations."
        f"{source_ref_str}\n"
        "The deprecation warning will be elevated to an error starting July 23, 2025, at the earliest."
    )


def _inconsistent_type_modifier_in_binding_error(
    expected: TypeModifier,
    known_modifiers: dict[str, TypeModifier],
    source_ref: Optional[Union[SourceReference, str]] = None,
) -> str:
    actual = ", ".join(
        f"{name}: {modifier.name}" for name, modifier in known_modifiers.items()
    )
    source_ref_str = f"\n\tat {source_ref}" if source_ref else ""
    return (
        f"Inconsistent modifiers in variable binding: "
        f"Expected modifier: {expected.name}, Actual modifiers: {actual}"
        f"{source_ref_str}\n"
        "The deprecation warning will be elevated to an error starting July 23, 2025, at the earliest."
    )


class TypeModifierValidation(ModelVisitor):
    """
    This class assumes that function calls are topologically sorted, so it traverses
    the list of function calls and infers the type modifiers for each function call
    without going recursively into the function calls.
    The function definition ports are modified inplace.
    """

    def __init__(
        self, *, skip_validation: bool = False, support_unused_ports: bool = True
    ) -> None:
        self._signature_ports: dict[str, PortDeclaration] = dict()
        self._inferred_ports: dict[str, PortDeclaration] = dict()
        self._unchecked: set[str] = set()

        self._initialized_vars: dict[str, TypeModifier] = dict()
        self._bound_vars: list[set[str]] = []

        self._conjugation_context: bool = False
        self._support_unused_ports = (
            support_unused_ports  # could be turned off for debugging
        )
        self._skip_validation = skip_validation
        self._source_ref: Optional[Union[SourceReference, str]] = None

    @contextmanager
    def validate_ports(
        self, ports: Collection[PortDeclaration], unchecked: Collection[str]
    ) -> Iterator[bool]:
        for port in ports:
            if port.type_modifier is TypeModifier.Inferred:
                self._inferred_ports[port.name] = port
            else:
                self._signature_ports[port.name] = port
        self._unchecked.update(unchecked)

        yield len(self._inferred_ports) > 0 or (
            any(
                port.type_modifier is not TypeModifier.Mutable
                for port in self._signature_ports.values()
            )
            and not self._skip_validation
        )

        self._set_unused_as_const()
        self._signature_ports.clear()
        self._inferred_ports.clear()
        self._unchecked.clear()

    @contextmanager
    def conjugation_context(self) -> Iterator[None]:
        previous_context = self._conjugation_context
        self._conjugation_context = True
        try:
            yield
        finally:
            self._conjugation_context = previous_context

    @contextmanager
    def source_reference_context(
        self, source_ref: Optional[Union[SourceReference, str]]
    ) -> Iterator[None]:
        previous_source_ref = self._source_ref
        self._source_ref = source_ref
        try:
            yield
        finally:
            self._source_ref = previous_source_ref

    def _set_unused_as_const(self) -> None:
        unresolved_ports = [
            port
            for port in self._inferred_ports.values()
            if port.type_modifier is TypeModifier.Inferred
        ]
        if not self._support_unused_ports and len(unresolved_ports) > 0:
            raise ClassiqInternalExpansionError(
                f"Unresolved inferred ports detected: {', '.join(port.name for port in unresolved_ports)}. "
                "All ports must have their type modifiers resolved."
            )
        for port in unresolved_ports:
            port.type_modifier = TypeModifier.Const

    def _validate_modifier(self, candidate: str, modifier: TypeModifier) -> None:
        if self._conjugation_context and modifier is TypeModifier.Permutable:
            modifier = TypeModifier.Const

        if candidate in self._inferred_ports:
            self._inferred_ports[candidate].type_modifier = TypeModifier.and_(
                self._inferred_ports[candidate].type_modifier, modifier
            )
            return

        if self._skip_validation or candidate in self._unchecked:
            return

        if candidate in self._signature_ports:
            self._validate_signature_modifier(candidate, modifier)

        elif candidate in self._initialized_vars:
            self._initialized_vars[candidate] = TypeModifier.and_(
                self._initialized_vars[candidate], modifier
            )

    def _validate_signature_modifier(
        self, candidate: str, modifier: TypeModifier
    ) -> None:
        signature_modifier = self._signature_ports[candidate].type_modifier
        if signature_modifier is not TypeModifier.and_(signature_modifier, modifier):
            warnings.warn(
                _inconsistent_type_modifier_error(
                    candidate, signature_modifier, modifier, self._source_ref
                ),
                ClassiqDeprecationWarning,
                stacklevel=1,
            )

    def _add_initialized_modifier(self, var: str, modifier: TypeModifier) -> None:
        if var in self._inferred_ports or var in self._signature_ports:
            return
        if self._conjugation_context and modifier is TypeModifier.Permutable:
            modifier = TypeModifier.Const
        self._initialized_vars[var] = modifier

    def run(
        self,
        func_def: NativeFunctionDefinition,
        unchecked: Collection[str],
    ) -> None:
        with (
            self.validate_ports(
                func_def.port_declarations, unchecked
            ) as should_validate,
            self.source_reference_context(f"function '{func_def.name}'"),
        ):
            if should_validate:
                self.visit(func_def.body)
                self._update_bound_vars()

    def _update_bound_vars(self) -> None:
        merged_bound_vars = _merge_overlapping(self._bound_vars)
        for bound_vars in merged_bound_vars:
            reduced_modifier = self._get_reduced_modifier(bound_vars)
            for var in bound_vars:
                self._validate_modifier(var, reduced_modifier)

    def visit_QuantumFunctionCall(self, call: QuantumFunctionCall) -> None:
        with self.source_reference_context(call.source_ref):
            for handle, port in call.handles_with_params:
                self._validate_modifier(handle.name, port.type_modifier)
                if port.direction is PortDeclarationDirection.Output:
                    self._add_initialized_modifier(handle.name, port.type_modifier)

        if self._has_inputs(call):
            bound_vars = {
                handle.name
                for handle, port in call.handles_with_params
                if port.direction is not PortDeclarationDirection.Inout
                and handle.name not in self._unchecked
            }
            self._bound_vars.append(bound_vars)

    @staticmethod
    def _has_inputs(call: QuantumFunctionCall) -> bool:
        return any(
            port.direction is PortDeclarationDirection.Input
            for _, port in call.handles_with_params
        )

    def visit_Allocate(self, alloc: Allocate) -> None:
        with self.source_reference_context(alloc.source_ref):
            self._validate_modifier(alloc.target.name, TypeModifier.Permutable)
            self._add_initialized_modifier(alloc.target.name, TypeModifier.Permutable)

    def visit_BindOperation(self, bind_op: BindOperation) -> None:
        var_names = {
            handle.name
            for handle in itertools.chain(bind_op.in_handles, bind_op.out_handles)
            if handle.name not in self._unchecked
        }
        self._bound_vars.append(var_names)
        for handle in bind_op.out_handles:
            self._add_initialized_modifier(handle.name, TypeModifier.Inferred)

    def _get_reduced_modifier(self, bound_vars: set[str]) -> TypeModifier:
        signature_modifiers = {
            name: self._signature_ports[name].type_modifier
            for name in bound_vars.intersection(self._signature_ports)
        }
        known_inferred_modifiers = {
            name: self._inferred_ports[name].type_modifier
            for name in bound_vars.intersection(self._inferred_ports)
            if self._inferred_ports[name].type_modifier is not TypeModifier.Inferred
        }
        known_initialized_modifiers = {
            name: self._initialized_vars[name]
            for name in bound_vars.intersection(self._initialized_vars)
            if self._initialized_vars[name] is not TypeModifier.Inferred
        }
        known_modifiers = (
            signature_modifiers | known_inferred_modifiers | known_initialized_modifiers
        )
        min_modifier = self._get_min_modifier(list(known_modifiers.values()))
        if not all(
            type_modifier is min_modifier
            for type_modifier in signature_modifiers.values()
        ):
            warnings.warn(
                _inconsistent_type_modifier_in_binding_error(
                    min_modifier, known_modifiers, self._source_ref
                ),
                ClassiqDeprecationWarning,
                stacklevel=1,
            )

        return min_modifier

    @staticmethod
    def _get_min_modifier(modifiers: list[TypeModifier]) -> TypeModifier:
        if len(modifiers) == 0:
            return TypeModifier.Const
        elif len(modifiers) == 1:
            return modifiers[0]
        else:
            return functools.reduce(TypeModifier.and_, modifiers)

    @staticmethod
    def _extract_expr_vars(expr_op: QuantumExpressionOperation) -> list[str]:
        vrc = VarRefCollector(
            ignore_duplicated_handles=True, ignore_sympy_symbols=True, unevaluated=True
        )
        vrc.visit(ast.parse(expr_op.expression.expr))
        return [handle.name for handle in vrc.var_handles]

    def visit_ArithmeticOperation(self, arith: ArithmeticOperation) -> None:
        with self.source_reference_context(arith.source_ref):
            result_var = arith.result_var.name
            self._validate_modifier(result_var, TypeModifier.Permutable)
            for expr_var in self._extract_expr_vars(arith):
                self._validate_modifier(expr_var, TypeModifier.Const)
            if not arith.is_inplace:
                self._add_initialized_modifier(result_var, TypeModifier.Permutable)

    def visit_AmplitudeLoadingOperation(
        self, amp_load: AmplitudeLoadingOperation
    ) -> None:
        with self.source_reference_context(amp_load.source_ref):
            result_var = amp_load.result_var.name
            self._validate_modifier(result_var, TypeModifier.Mutable)
            for expr_var in self._extract_expr_vars(amp_load):
                self._validate_modifier(expr_var, TypeModifier.Const)

    def visit_PhaseOperation(self, phase_op: PhaseOperation) -> None:
        with self.source_reference_context(phase_op.source_ref):
            for expr_var in self._extract_expr_vars(phase_op):
                self._validate_modifier(expr_var, TypeModifier.Const)

    def visit_Control(self, control: Control) -> None:
        with self.source_reference_context(control.source_ref):
            for control_var in self._extract_expr_vars(control):
                self._validate_modifier(control_var, TypeModifier.Const)
            self.visit(control.body)
            if control.else_block is not None:
                self.visit(control.else_block)

    def visit_Invert(self, invert: Invert) -> None:
        with self.source_reference_context(invert.source_ref):
            self.visit(invert.body)

    def visit_Power(self, power: Power) -> None:
        with self.source_reference_context(power.source_ref):
            self.visit(power.body)

    def visit_WithinApply(self, within_apply: WithinApply) -> None:
        with self.source_reference_context(within_apply.source_ref):
            with self.conjugation_context():
                self.visit(within_apply.compute)
            self.visit(within_apply.action)

    def visit_Block(self, block: Block) -> None:
        with self.source_reference_context(block.source_ref):
            self.visit(block.statements)


def _merge_overlapping(bound_vars: Sequence[Collection[str]]) -> list[set[str]]:
    """
    Merges overlapping sets of bound variables.
    Two sets overlap if they share at least one variable.
    """
    all_bound_vars = bound_vars
    merged_bound_vars: list[set[str]] = []
    loop_guard: int = 10
    idx: int = 0

    for _ in range(loop_guard):
        idx += 1

        merged_bound_vars = []
        modified: bool = False
        for current_bound_vars in all_bound_vars:
            for existing in merged_bound_vars:
                if existing.intersection(current_bound_vars):
                    existing.update(current_bound_vars)
                    modified = True
                    break
            else:
                merged_bound_vars.append(set(current_bound_vars))

        if not modified:
            break
        all_bound_vars = merged_bound_vars

    if idx == loop_guard - 1:
        raise ClassiqInternalExpansionError

    return merged_bound_vars
