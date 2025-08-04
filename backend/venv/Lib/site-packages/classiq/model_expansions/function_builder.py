from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.compiler_keywords import (
    EXPANDED_KEYWORD,
    LAMBDA_KEYWORD,
)
from classiq.interface.generator.functions.builtins.internal_operators import (
    BLOCK_OPERATOR_NAME,
    WITHIN_APPLY_NAME,
)
from classiq.interface.model.model import MAIN_FUNCTION_NAME
from classiq.interface.model.native_function_definition import (
    NativeFunctionDefinition,
)
from classiq.interface.model.quantum_function_declaration import (
    PositionalArg,
)
from classiq.interface.model.quantum_statement import QuantumStatement
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)
from classiq.interface.source_reference import SourceReference

from classiq.model_expansions.capturing.captured_vars import (
    CapturedVars,
    validate_captured_directions,
    validate_end_state,
)
from classiq.model_expansions.closure import Closure, FunctionClosure
from classiq.model_expansions.scope import Scope
from classiq.model_expansions.utils.counted_name_allocator import CountedNameAllocator

ClosureType = TypeVar("ClosureType", bound=Closure)

BLOCKS_ALLOWED_CAPTURING = (WITHIN_APPLY_NAME, BLOCK_OPERATOR_NAME)


@dataclass
class Block:
    statements: list[QuantumStatement] = field(default_factory=list)
    captured_vars: CapturedVars = field(default_factory=CapturedVars)

    @property
    def variable_declarations(self) -> list[VariableDeclarationStatement]:
        return [
            stmt
            for stmt in self.statements
            if isinstance(stmt, VariableDeclarationStatement)
        ]


@dataclass
class OperationContext(Generic[ClosureType]):
    closure: ClosureType
    blocks: dict[str, Block] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.closure.name

    @property
    def positional_arg_declarations(self) -> Sequence[PositionalArg]:
        return self.closure.positional_arg_declarations

    def statements(self, block_name: str) -> list[QuantumStatement]:
        return self.blocks[block_name].statements


@dataclass
class FunctionContext(OperationContext[FunctionClosure]):
    @classmethod
    def create(cls, original_function: FunctionClosure) -> "FunctionContext":
        return cls(original_function, {"body": Block()})

    @property
    def body(self) -> list[QuantumStatement]:
        return self.statements("body")

    @property
    def is_lambda(self) -> bool:
        return self.closure.is_lambda


class OperationBuilder:
    def __init__(
        self, functions_scope: Scope, counted_name_allocator: CountedNameAllocator
    ) -> None:
        self._operations: list[OperationContext] = []
        self._blocks: list[str] = []
        self._functions_scope = functions_scope
        self._current_source_ref: Optional[SourceReference] = None
        self._counted_name_allocator = counted_name_allocator

    @property
    def current_operation(self) -> Closure:
        return self._operations[-1].closure

    @property
    def current_scope(self) -> Scope:
        return self.current_operation.scope

    @property
    def current_function(self) -> FunctionClosure:
        return self._get_last_function(self._operations)

    @property
    def parent_function(self) -> FunctionClosure:
        return self._get_last_function(self._operations[:-1])

    @staticmethod
    def _get_last_function(operations: list[OperationContext]) -> FunctionClosure:
        for operation in reversed(operations):
            if isinstance(operation.closure, FunctionClosure):
                return operation.closure
        raise ClassiqInternalExpansionError("No function found")

    @property
    def current_block(self) -> Block:
        return self._operations[-1].blocks[self._blocks[-1]]

    @property
    def _current_statements(self) -> list[QuantumStatement]:
        return self.current_block.statements

    def emit_statement(self, statement: QuantumStatement) -> None:
        if self._current_source_ref is not None:
            statement.source_ref = self._current_source_ref
        self._current_statements.append(statement)

    @property
    def current_statement(self) -> QuantumStatement:
        return self._current_statements[-1]

    @contextmanager
    def block_context(self, block_name: str) -> Iterator[None]:
        self._blocks.append(block_name)
        block = Block()
        block.captured_vars.set_parent(self.current_operation.captured_vars)
        self._operations[-1].blocks[block_name] = block
        yield
        captured_vars = self.current_block.captured_vars
        if (
            not isinstance(self.current_operation, FunctionClosure)
            and self.current_operation.name not in BLOCKS_ALLOWED_CAPTURING
        ):
            validate_captured_directions(
                captured_vars.filter_var_decls(
                    self.current_block.variable_declarations
                ),
                report_outin=False,
            )
        self.current_operation.captured_vars.update(captured_vars)
        self._blocks.pop()

    @contextmanager
    def operation_context(
        self, original_operation: Closure
    ) -> Iterator[OperationContext]:
        context: OperationContext
        if isinstance(original_operation, FunctionClosure):
            context = FunctionContext.create(original_operation)
            context.closure.captured_vars.init_params(original_operation)
        else:
            context = OperationContext(closure=original_operation)
            context.closure.captured_vars.set_parent(self.current_block.captured_vars)
        self._operations.append(context)
        yield context
        self._finalize_within_apply()
        if isinstance(self.current_operation, FunctionClosure):
            validate_end_state(
                self.current_operation, self.current_operation.captured_vars
            )
        self._propagate_captured_vars()
        self._operations.pop()

    def _finalize_within_apply(self) -> None:
        if self.current_operation.name != WITHIN_APPLY_NAME:
            return
        within_captured_vars = self._operations[-1].blocks["within"].captured_vars
        self.current_operation.captured_vars.update(within_captured_vars.negate())

    def _propagate_captured_vars(self) -> None:
        captured_vars = self.current_operation.captured_vars
        if isinstance(self.current_operation, FunctionClosure):
            captured_vars = captured_vars.filter_vars(
                self.current_function
            ).set_propagated()
            validate_captured_directions(captured_vars)
        if len(self._operations) < 2:
            return
        parent_block = self._operations[-2].blocks[self._blocks[-1]]
        parent_block.captured_vars.update(captured_vars)

    @contextmanager
    def source_ref_context(
        self, source_ref: Optional[SourceReference]
    ) -> Iterator[None]:
        previous_source_ref = self._current_source_ref
        self._current_source_ref = source_ref
        yield
        self._current_source_ref = previous_source_ref

    def create_definition(
        self, function_context: FunctionContext, params: Sequence[PositionalArg]
    ) -> NativeFunctionDefinition:
        name = self._get_expanded_function_name(function_context)

        return NativeFunctionDefinition(
            name=name,
            body=function_context.body,
            positional_arg_declarations=params,
        )

    def _get_expanded_function_name(self, function_context: FunctionContext) -> str:
        name = function_context.name

        if name == MAIN_FUNCTION_NAME:
            return name

        for _ in self.current_scope:
            name = self._counted_name_allocator.allocate(
                f"{name}_{LAMBDA_KEYWORD + '_0_0_' if function_context.is_lambda else ''}{EXPANDED_KEYWORD}"
            )
            if name not in self.current_scope:
                break
        else:
            raise ClassiqInternalExpansionError("Could not allocate function name")

        return name
