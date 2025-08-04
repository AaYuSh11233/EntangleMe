from collections.abc import Mapping
from typing import Optional, Union

from classiq.interface.constants import DEFAULT_DECIMAL_PRECISION
from classiq.interface.exceptions import ClassiqInternalError
from classiq.interface.generator.constant import Constant
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    Integer,
    Real,
)
from classiq.interface.generator.functions.concrete_types import (
    ConcreteClassicalType,
    ConcreteQuantumType,
)
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.functions.type_name import TypeName
from classiq.interface.generator.types.compilation_metadata import CompilationMetadata
from classiq.interface.generator.types.enum_declaration import EnumDeclaration
from classiq.interface.generator.types.qstruct_declaration import QStructDeclaration
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.generator.visitor import NodeType
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.bounds import SetBoundsStatement
from classiq.interface.model.classical_if import ClassicalIf
from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
)
from classiq.interface.model.control import Control
from classiq.interface.model.handle_binding import (
    FieldHandleBinding,
    HandleBinding,
    HandlesList,
    SlicedHandleBinding,
    SubscriptHandleBinding,
)
from classiq.interface.model.inplace_binary_operation import InplaceBinaryOperation
from classiq.interface.model.invert import Invert
from classiq.interface.model.model import Model
from classiq.interface.model.model_visitor import ModelVisitor
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.phase_operation import PhaseOperation
from classiq.interface.model.port_declaration import (
    AnonPortDeclaration,
)
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
    ArithmeticOperationKind,
)
from classiq.interface.model.quantum_function_call import (
    QuantumFunctionCall,
)
from classiq.interface.model.quantum_function_declaration import (
    AnonQuantumFunctionDeclaration,
    AnonQuantumOperandDeclaration,
    QuantumFunctionDeclaration,
    QuantumOperandDeclaration,
)
from classiq.interface.model.quantum_lambda_function import (
    OperandIdentifier,
    QuantumLambdaFunction,
)
from classiq.interface.model.quantum_type import (
    QuantumBit,
    QuantumBitvector,
    QuantumNumeric,
)
from classiq.interface.model.repeat import Repeat
from classiq.interface.model.statement_block import StatementBlock
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)
from classiq.interface.model.within_apply_operation import WithinApply
from classiq.interface.pretty_print.expression_to_qmod import transform_expression

from classiq.open_library.functions import OPEN_LIBRARY_FUNCTIONS
from classiq.qmod.semantics.annotation.call_annotation import resolve_function_calls


class DSLPrettyPrinter(ModelVisitor):
    def __init__(
        self,
        decimal_precision: Optional[int] = DEFAULT_DECIMAL_PRECISION,
        emit_open_lib_functions: bool = False,
        compilation_metadata: Optional[dict[str, CompilationMetadata]] = None,
    ) -> None:
        self._level = 0
        self._decimal_precision = decimal_precision
        self._emit_open_lib_functions = emit_open_lib_functions
        self._compilation_metadata: dict[str, CompilationMetadata] = (
            compilation_metadata or {}
        )

    def visit(self, node: NodeType) -> str:
        res = super().visit(node)
        if not isinstance(res, str):
            raise AssertionError(f"Pretty printing for {type(node)} is not supported ")
        return res

    def visit_Model(self, model: Model) -> str:
        # FIXME - CAD-20149: Remove this line once the froggies are removed, and the visit of lambdas can be done without accessing the func_decl property (with rename_params values only).
        resolve_function_calls(model, model.function_dict)
        self._compilation_metadata = model.functions_compilation_metadata

        enum_decls = [self.visit(enum_decl) for enum_decl in model.enums]
        struct_decls = [self.visit(struct_decl) for struct_decl in model.types]
        qstruct_decls = [self.visit(qstruct_decl) for qstruct_decl in model.qstructs]
        func_defs = [self.visit(func_def) for func_def in model.functions]
        constants = [self.visit(constant) for constant in model.constants]
        classical_code = (
            [f"cscope ```\n{model.classical_execution_code}\n```\n"]
            if model.classical_execution_code
            else []
        )

        items = [
            *constants,
            *enum_decls,
            *struct_decls,
            *qstruct_decls,
            *func_defs,
            *classical_code,
        ]
        return "\n".join([item for item in items if item != ""])

    def visit_Constant(self, constant: Constant) -> str:
        return f"{self._indent}{self.visit(constant.name)}: {self.visit(constant.const_type)} = {self.visit(constant.value)};\n"

    def _visit_arg_decls(self, func_def: AnonQuantumFunctionDeclaration) -> str:
        positional_args = ", ".join(
            self.visit(arg_decl) for arg_decl in func_def.positional_arg_declarations
        )
        return f"({positional_args})"

    def _get_unchecked_string(self, func_decl: QuantumFunctionDeclaration) -> str:
        if func_decl.name not in self._compilation_metadata:
            return ""
        unchecked = self._compilation_metadata[func_decl.name].unchecked
        if len(unchecked) == 0:
            return ""
        return f" unchecked ({', '.join(unchecked)})\n"

    def visit_QuantumFunctionDeclaration(
        self, func_decl: QuantumFunctionDeclaration
    ) -> str:
        unchecked = self._get_unchecked_string(func_decl)
        return f"qfunc {func_decl.name}{self._visit_arg_decls(func_decl)}{unchecked}"

    def visit_EnumDeclaration(self, enum_decl: EnumDeclaration) -> str:
        return f"enum {enum_decl.name} {{\n{self._visit_members(enum_decl.members)}}}\n"

    def _visit_members(self, members: dict[str, int]) -> str:
        self._level += 1
        members_str = "".join(
            f"{self._indent}{self.visit(member_name)} = {member_value};\n"
            for member_name, member_value in members.items()
        )
        self._level -= 1
        return members_str

    def visit_StructDeclaration(self, struct_decl: StructDeclaration) -> str:
        return f"struct {struct_decl.name} {{\n{self._visit_variables(struct_decl.variables)}}}\n"

    def visit_QStructDeclaration(self, qstruct_decl: QStructDeclaration) -> str:
        return f"qstruct {qstruct_decl.name} {{\n{self._visit_variables(qstruct_decl.fields)}}}\n"

    def _visit_variables(
        self, variables: Mapping[str, Union[ConcreteClassicalType, ConcreteQuantumType]]
    ) -> str:
        self._level += 1
        variables_str = "".join(
            f"{self._indent}{self.visit(field_name)}: {self.visit(var_decl)};\n"
            for field_name, var_decl in variables.items()
        )
        self._level -= 1
        return variables_str

    def visit_AnonPortDeclaration(self, port_decl: AnonPortDeclaration) -> str:
        modifier_str = (
            f"{port_decl.type_modifier} "
            if port_decl.type_modifier in [TypeModifier.Const, TypeModifier.Permutable]
            else ""
        )
        dir_str = (
            f"{port_decl.direction} "
            if port_decl.direction is not PortDeclarationDirection.Inout
            else ""
        )
        param_name = f"{port_decl.name}: " if port_decl.name is not None else ""
        return (
            f"{modifier_str}{dir_str}{param_name}{self.visit(port_decl.quantum_type)}"
        )

    def visit_QuantumBit(self, qtype: QuantumBit) -> str:
        return "qbit"

    def visit_QuantumBitvector(self, qtype: QuantumBitvector) -> str:
        element_type = self.visit(qtype.element_type)
        if qtype.length is not None:
            return f"{element_type}[{self.visit(qtype.length)}]"
        return f"{element_type}[]"

    def visit_QuantumNumeric(self, qtype: QuantumNumeric) -> str:
        params = ""
        if qtype.size is not None:
            params = "<{}>".format(
                ", ".join(
                    self.visit(param)
                    for param in [qtype.size, qtype.is_signed, qtype.fraction_digits]
                    if param is not None
                )
            )

        return f"qnum{params}"

    def visit_AnonClassicalParameterDeclaration(
        self, cparam: AnonClassicalParameterDeclaration
    ) -> str:
        param_name = f"{cparam.name}: " if cparam.name is not None else ""
        return f"{param_name}{self.visit(cparam.classical_type)}"

    def visit_Integer(self, ctint: Integer) -> str:
        return "int"

    def visit_Real(self, ctint: Real) -> str:
        return "real"

    def visit_Bool(self, ctbool: Bool) -> str:
        return "bool"

    def visit_ClassicalArray(self, ctarray: ClassicalArray) -> str:
        element_type = self.visit(ctarray.element_type)
        if ctarray.length is not None:
            return f"{element_type}[{self.visit(ctarray.length)}]"
        return f"{element_type}[]"

    def visit_ClassicalTuple(self, classical_tuple: ClassicalTuple) -> str:
        raw_type = classical_tuple.get_raw_type()
        if isinstance(raw_type, ClassicalTuple):
            raise ClassiqInternalError("Empty tuple pretty-print not supported")
        return self.visit(raw_type)

    def visit_TypeName(self, type_: TypeName) -> str:
        return type_.name

    def visit_VariableDeclarationStatement(
        self, var_decl: VariableDeclarationStatement
    ) -> str:
        return f"{self._indent}{var_decl.name}: {self.visit(var_decl.qmod_type)};\n"

    def visit_AnonQuantumOperandDeclaration(
        self, op_decl: AnonQuantumOperandDeclaration
    ) -> str:
        param_name = f"{op_decl.name}: " if op_decl.name is not None else ""
        return f"{param_name}qfunc{[] if op_decl.is_list else ''} {self._visit_arg_decls(op_decl)}"

    def visit_QuantumOperandDeclaration(
        self, op_decl: QuantumOperandDeclaration
    ) -> str:
        return self.visit_AnonQuantumOperandDeclaration(op_decl)

    def visit_NativeFunctionDefinition(self, func_def: NativeFunctionDefinition) -> str:
        if not self._emit_open_lib_functions and func_def.name in [
            qfunc_.func_decl.name for qfunc_ in OPEN_LIBRARY_FUNCTIONS
        ]:
            return ""
        self._level += 1
        body = "".join(self.visit(qvar_decl) for qvar_decl in func_def.body)
        self._level -= 1
        return f"{self.visit_QuantumFunctionDeclaration(func_def)} {{\n{body}}}\n"

    def visit_Allocate(self, allocate: Allocate) -> str:
        params = ", ".join(
            self.visit(param)
            for param in [
                allocate.size,
                allocate.is_signed,
                allocate.fraction_digits,
                allocate.target,
            ]
            if param is not None
        )
        return f"{self._indent}allocate({params});\n"

    def visit_QuantumFunctionCall(self, func_call: QuantumFunctionCall) -> str:
        positional_args = ", ".join(
            self.visit(arg_decl) for arg_decl in func_call.positional_args
        )
        return f"{self._indent}{func_call.func_name}{f'[{self.visit(func_call.function.index)}]' if isinstance(func_call.function, OperandIdentifier) else ''}({positional_args});\n"

    def visit_Control(self, op: Control) -> str:
        control = f"{self._indent}control ({self.visit(op.expression)}) {{\n"
        control += self._visit_body(op.body)
        control += f"{self._indent}}}"
        if op.else_block is not None:
            control += " else {\n"
            control += self._visit_body(op.else_block)
            control += f"{self._indent}}}"
        control += "\n"
        return control

    def visit_PhaseOperation(self, op: PhaseOperation) -> str:
        theta = f", {self.visit(op.theta)}" if op.theta else ""
        phase = f"{self._indent}phase ({self.visit(op.expression)}{theta});\n"
        return phase

    def visit_ClassicalIf(self, op: ClassicalIf) -> str:
        classical_if = f"{self._indent}if ({self.visit(op.condition)}) {{\n"
        classical_if += self._visit_body(op.then)

        if op.else_:
            classical_if += f"{self._indent}}} else {{\n"
            classical_if += self._visit_body(op.else_)

        classical_if += f"{self._indent}}}\n"
        return classical_if

    def visit_WithinApply(self, op: WithinApply) -> str:
        within_apply_code = f"{self._indent}within {{\n"
        within_apply_code += self._visit_body(op.compute)
        within_apply_code += f"{self._indent}}} apply {{\n"
        within_apply_code += self._visit_body(op.action)
        within_apply_code += f"{self._indent}}}\n"
        return within_apply_code

    def visit_Repeat(self, repeat: Repeat) -> str:
        repeat_code = f"{self._indent}repeat ({self.visit(repeat.iter_var)}: {self.visit(repeat.count)}) {{\n"
        repeat_code += self._visit_body(repeat.body)
        repeat_code += f"{self._indent}}}\n"
        return repeat_code

    def visit_Power(self, power: Power) -> str:
        power_code = f"{self._indent}power ({self.visit(power.power)}) {{\n"
        power_code += self._visit_body(power.body)
        power_code += f"{self._indent}}}\n"
        return power_code

    def visit_Invert(self, invert: Invert) -> str:
        invert_code = f"{self._indent}invert {{\n"
        invert_code += self._visit_body(invert.body)
        invert_code += f"{self._indent}}}\n"
        return invert_code

    def visit_Block(self, block: Block) -> str:
        block_code = f"{self._indent}{{\n"
        block_code += self._visit_body(block.statements)
        block_code += f"{self._indent}}}\n"
        return block_code

    def _visit_body(self, body: StatementBlock) -> str:
        code = ""
        self._level += 1
        for statement in body:
            code += self.visit(statement)
        self._level -= 1
        return code

    def visit_InplaceBinaryOperation(self, op: InplaceBinaryOperation) -> str:
        return f"{self._indent}{op.operation.value}({self.visit(op.value)}, {self.visit(op.target)});\n"

    def _visit_pack_expr(self, vars: list[HandleBinding]) -> str:
        if len(vars) == 1:
            return self.visit(vars[0])

        var_list_str = ", ".join(self.visit(var) for var in vars)
        return f"{{{var_list_str}}}"

    def visit_Expression(self, expr: Expression) -> str:
        return transform_expression(
            expr.expr, level=self._level, decimal_precision=self._decimal_precision
        )

    def visit_QuantumLambdaFunction(self, qlambda: QuantumLambdaFunction) -> str:
        positional_args = ", ".join(
            qlambda.pos_rename_params[idx]
            for idx, arg_decl in enumerate(
                qlambda.func_decl.positional_arg_declarations
            )
        )
        body = self._visit_body(qlambda.body)
        return f"lambda({positional_args}) {{\n{body}{self._indent}}}"

    def visit_HandleBinding(self, var_ref: HandleBinding) -> str:
        return var_ref.name

    def visit_SlicedHandleBinding(self, var_ref: SlicedHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}[{self.visit(var_ref.start)}:{self.visit(var_ref.end)}]"

    def visit_SubscriptHandleBinding(self, var_ref: SubscriptHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}[{self.visit(var_ref.index)}]"

    def visit_FieldHandleBinding(self, var_ref: FieldHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}.{self.visit(var_ref.field)}"

    def visit_HandlesList(self, handles: HandlesList) -> str:
        return f"{{{', '.join(map(self.visit, handles.handles))}}}"

    def visit_ArithmeticOperation(self, arith_op: ArithmeticOperation) -> str:
        if arith_op.operation_kind == ArithmeticOperationKind.Assignment:
            op = "="
        elif arith_op.operation_kind == ArithmeticOperationKind.InplaceXor:
            op = "^="
        else:
            op = "+="
        return f"{self._indent}{self.visit(arith_op.result_var)} {op} {self.visit(arith_op.expression)};\n"

    def visit_AmplitudeLoadingOperation(
        self, amplitude_loading_op: AmplitudeLoadingOperation
    ) -> str:
        return f"{self._indent}{self.visit(amplitude_loading_op.result_var)} *= {self.visit(amplitude_loading_op.expression)};\n"

    def _print_bind_handles(self, handles: list[HandleBinding]) -> str:
        if len(handles) == 1:
            return self.visit(handles[0])

        return "{" + ", ".join(self.visit(handle) for handle in handles) + "}"

    def visit_BindOperation(self, bind_op: BindOperation) -> str:
        return f"{self._indent}{self._print_bind_handles(bind_op.in_handles)} -> {self._print_bind_handles(bind_op.out_handles)};\n"

    def visit_list(self, node: list) -> str:
        return "[" + ", ".join(self.visit(elem) for elem in node) + "]"

    def visit_OperandIdentifier(self, op: OperandIdentifier) -> str:
        return str(op)

    def visit_SetBoundsStatement(self, op: SetBoundsStatement) -> str:
        target = self.visit(op.target)
        if op.lower_bound is None or op.upper_bound is None:
            return f"{self._indent}reset_bounds({target});\n"
        else:
            lower_bound = self.visit(op.lower_bound)
            upper_bound = self.visit(op.upper_bound)
            return (
                f"{self._indent}reset_bounds({target}, {lower_bound}, {upper_bound});\n"
            )

    @property
    def _indent(self) -> str:
        return "  " * self._level
