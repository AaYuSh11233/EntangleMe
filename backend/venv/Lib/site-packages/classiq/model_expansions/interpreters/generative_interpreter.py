from functools import singledispatchmethod
from typing import Any, Optional

import numpy as np
from numpy.random import permutation

from classiq.interface.generator.constant import Constant
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.builtins.internal_operators import (
    BLOCK_OPERATOR_NAME,
    CLASSICAL_IF_OPERATOR_NAME,
    CONTROL_OPERATOR_NAME,
    INVERT_OPERATOR_NAME,
    REPEAT_OPERATOR_NAME,
    WITHIN_APPLY_NAME,
)
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.bounds import SetBoundsStatement
from classiq.interface.model.classical_if import ClassicalIf
from classiq.interface.model.control import Control
from classiq.interface.model.inplace_binary_operation import InplaceBinaryOperation
from classiq.interface.model.invert import Invert
from classiq.interface.model.model import Model
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.phase_operation import PhaseOperation
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
)
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_lambda_function import (
    OperandIdentifier,
    QuantumLambdaFunction,
)
from classiq.interface.model.quantum_statement import QuantumStatement
from classiq.interface.model.repeat import Repeat
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)
from classiq.interface.model.within_apply_operation import WithinApply

from classiq.model_expansions.closure import (
    Closure,
    FunctionClosure,
    GenerativeClosure,
    GenerativeFunctionClosure,
)
from classiq.model_expansions.generative_functions import emit_generative_statements
from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter
from classiq.model_expansions.quantum_operations import (
    BindEmitter,
    QuantumFunctionCallEmitter,
    VariableDeclarationStatementEmitter,
)
from classiq.model_expansions.quantum_operations.allocate import AllocateEmitter
from classiq.model_expansions.quantum_operations.assignment_result_processor import (
    AssignmentResultProcessor,
)
from classiq.model_expansions.quantum_operations.block_evaluator import (
    BlockEvaluator,
    IfElimination,
    RepeatElimination,
)
from classiq.model_expansions.quantum_operations.bounds import SetBoundsEmitter
from classiq.model_expansions.quantum_operations.classical_var_emitter import (
    ClassicalVarEmitter,
)
from classiq.model_expansions.quantum_operations.composite_emitter import (
    CompositeEmitter,
)
from classiq.model_expansions.quantum_operations.expression_evaluator import (
    ExpressionEvaluator,
)
from classiq.model_expansions.quantum_operations.handle_evaluator import HandleEvaluator
from classiq.model_expansions.quantum_operations.repeat_block_evaluator import (
    RepeatBlockEvaluator,
)
from classiq.model_expansions.scope import Evaluated, Scope
from classiq.model_expansions.scope_initialization import (
    add_constants_to_scope,
    add_functions_to_scope,
    add_generative_functions_to_scope,
)
from classiq.qmod.builtins.functions import permute
from classiq.qmod.model_state_container import ModelStateContainer
from classiq.qmod.quantum_function import GenerativeQFunc
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator


class GenerativeInterpreter(BaseInterpreter):
    def __init__(
        self,
        model: Model,
        generative_functions: list[GenerativeQFunc],
    ) -> None:
        super().__init__(model)
        add_generative_functions_to_scope(
            generative_functions, self._top_level_scope, override_atomic=True
        )
        self.infer_symbolic_parameters(
            model.functions, [gen_func.func_decl for gen_func in generative_functions]
        )

    def infer_symbolic_parameters(
        self,
        functions: list[NativeFunctionDefinition],
        additional_signatures: Optional[
            list[NamedParamsQuantumFunctionDeclaration]
        ] = None,
    ) -> None:
        pass

    def evaluate_lambda(self, function: QuantumLambdaFunction) -> Evaluated:
        func_decl = NamedParamsQuantumFunctionDeclaration(
            name=self._counted_name_allocator.allocate(
                function.func_decl.name or "<lambda>"
            ),
            positional_arg_declarations=function.named_func_decl.positional_arg_declarations,
        )

        closure_class: type[FunctionClosure]
        extra_args: dict[str, Any]
        if function.is_generative():
            closure_class = GenerativeFunctionClosure
            extra_args = {
                "generative_blocks": {
                    "body": GenerativeQFunc(function.py_callable, func_decl),
                }
            }
        else:
            closure_class = FunctionClosure
            extra_args = {}

        closure = closure_class.create(
            name=func_decl.name,
            positional_arg_declarations=func_decl.positional_arg_declarations,
            body=function.body,
            scope=Scope(parent=self._builder.current_scope),
            lambda_external_vars=self._builder.current_block.captured_vars,
            **extra_args,
        )
        return Evaluated(
            value=closure,
            defining_function=self._builder.current_function,
        )

    @singledispatchmethod
    def emit(self, statement: QuantumStatement) -> None:  # type:ignore[override]
        raise NotImplementedError(f"Cannot emit {statement!r}")

    @emit.register
    def _emit_quantum_function_call(self, call: QuantumFunctionCall) -> None:
        self.emit_quantum_function_call(call)

    def emit_quantum_function_call(self, call: QuantumFunctionCall) -> None:
        QuantumFunctionCallEmitter(self).emit(call)

    @emit.register
    def _emit_allocate(self, allocate: Allocate) -> None:
        return self.emit_allocate(allocate)

    def emit_allocate(self, allocate: Allocate) -> None:
        AllocateEmitter(self).emit(allocate)

    @emit.register
    def _emit_bind(self, bind: BindOperation) -> None:
        self.emit_bind(bind)

    def emit_bind(self, bind: BindOperation) -> None:
        BindEmitter(self).emit(bind)

    @emit.register
    def emit_amplitude_loading_operation(self, op: AmplitudeLoadingOperation) -> None:
        CompositeEmitter[AmplitudeLoadingOperation](
            self,
            [
                HandleEvaluator(self, "result_var"),
                ExpressionEvaluator(self, "expression"),
                AssignmentResultProcessor(self),
            ],
        ).emit(op)

    @emit.register
    def _emit_arithmetic_operation(self, op: ArithmeticOperation) -> None:
        self.emit_arithmetic_operation(op)

    def emit_arithmetic_operation(self, op: ArithmeticOperation) -> None:
        CompositeEmitter[ArithmeticOperation](
            self,
            [
                HandleEvaluator(self, "result_var"),
                ExpressionEvaluator(self, "expression"),
                ClassicalVarEmitter(self),
                AssignmentResultProcessor(self),
            ],
        ).emit(op)

    @emit.register
    def emit_inplace_binary_operation(self, op: InplaceBinaryOperation) -> None:
        CompositeEmitter[InplaceBinaryOperation](
            self,
            [
                HandleEvaluator(self, "target"),
                HandleEvaluator(self, "value"),
                ExpressionEvaluator(self, "value"),
            ],
        ).emit(op)

    @emit.register
    def emit_variable_declaration(
        self, variable_declaration: VariableDeclarationStatement
    ) -> None:
        VariableDeclarationStatementEmitter(self).emit(variable_declaration)

    @emit.register
    def _emit_classical_if(self, classical_if: ClassicalIf) -> None:
        self.emit_classical_if(classical_if)

    def emit_classical_if(self, classical_if: ClassicalIf) -> None:
        CompositeEmitter[ClassicalIf](
            self,
            [
                ExpressionEvaluator(self, "condition"),
                IfElimination(self),
                BlockEvaluator(
                    self,
                    CLASSICAL_IF_OPERATOR_NAME,
                    "then",
                    "else_",
                ),
            ],
        ).emit(classical_if)

    @emit.register
    def emit_within_apply(self, within_apply: WithinApply) -> None:
        BlockEvaluator(
            self,
            WITHIN_APPLY_NAME,
            "within",
            "apply",
            "compute",
            "action",
        ).emit(within_apply)

    @emit.register
    def emit_invert(self, invert: Invert) -> None:
        BlockEvaluator(self, INVERT_OPERATOR_NAME, "body").emit(invert)

    @emit.register
    def _emit_repeat(self, repeat: Repeat) -> None:
        self.emit_repeat(repeat)

    def emit_repeat(self, repeat: Repeat) -> None:
        CompositeEmitter[Repeat](
            self,
            [
                ExpressionEvaluator(self, "count"),
                RepeatElimination(self),
                RepeatBlockEvaluator(self, REPEAT_OPERATOR_NAME, "body"),
            ],
        ).emit(repeat)

    @emit.register
    def _emit_control(self, control: Control) -> None:
        self.emit_control(control)

    def emit_control(self, control: Control) -> None:
        CompositeEmitter[Control](
            self,
            [
                ExpressionEvaluator(self, "expression"),
                BlockEvaluator(
                    self,
                    CONTROL_OPERATOR_NAME,
                    "body",
                    "else_block",
                ),
            ],
        ).emit(control)

    @emit.register
    def emit_power(self, power: Power) -> None:
        CompositeEmitter[Power](
            self,
            [
                ExpressionEvaluator(self, "power"),
                BlockEvaluator(self, CONTROL_OPERATOR_NAME, "body"),
            ],
        ).emit(power)

    @emit.register
    def emit_phase(self, phase: PhaseOperation) -> None:
        CompositeEmitter[PhaseOperation](
            self,
            [
                ExpressionEvaluator(self, "expression"),
                ExpressionEvaluator(self, "theta"),
            ],
        ).emit(phase)

    @emit.register
    def emit_set_bounds(self, op: SetBoundsStatement) -> None:
        CompositeEmitter[SetBoundsStatement](
            self,
            [
                ExpressionEvaluator(self, "lower_bound"),
                ExpressionEvaluator(self, "upper_bound"),
                HandleEvaluator(self, "target"),
                SetBoundsEmitter(self),
            ],
        ).emit(op)

    @emit.register
    def emit_block(self, block: Block) -> None:
        BlockEvaluator(self, BLOCK_OPERATOR_NAME, "statements").emit(block)

    def _expand_body(self, operation: Closure) -> None:
        if isinstance(operation, FunctionClosure) and operation.name == "permute":
            # special expansion since permute is generative
            self._expand_permute()
        elif isinstance(operation, GenerativeClosure):
            args = [
                self.evaluate(param.name)
                for param in operation.positional_arg_declarations
            ]
            emit_generative_statements(self, operation, args)
        else:
            super()._expand_body(operation)

    def _expand_permute(self) -> None:
        functions = self.evaluate("functions").as_type(list)
        functions_permutation = permutation(np.array(range(len(functions))))
        calls: list[QuantumFunctionCall] = []
        for function_index in functions_permutation:
            permute_call = QuantumFunctionCall(
                function=OperandIdentifier(
                    name="functions", index=Expression(expr=f"{function_index}")
                )
            )
            permute_call.set_func_decl(permute.func_decl)
            calls.append(permute_call)
        self._expand_block(calls, "body")

    def update_generative_functions(
        self, generative_functions: dict[str, GenerativeQFunc]
    ) -> None:
        add_generative_functions_to_scope(
            list(generative_functions.values()), self._top_level_scope
        )
        for name, gen_func in generative_functions.items():
            if gen_func.compilation_metadata is not None:
                self._functions_compilation_metadata[name] = (
                    gen_func.compilation_metadata
                )

    def update_declarative_functions(
        self,
        functions: dict[str, NativeFunctionDefinition],
        qmodule: ModelStateContainer,
    ) -> None:
        add_functions_to_scope(list(functions.values()), self._top_level_scope)
        for dec_func_name in functions:
            if dec_func_name in qmodule.functions_compilation_metadata:
                self._functions_compilation_metadata[dec_func_name] = (
                    qmodule.functions_compilation_metadata[dec_func_name]
                )

    def add_constant(self, constant: Constant) -> None:
        QStructAnnotator().visit(constant.const_type)
        add_constants_to_scope([constant], self._top_level_scope)
