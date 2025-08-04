from collections.abc import Mapping
from typing import Optional, Union, cast

import black

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
from classiq.interface.generator.visitor import NodeType, Visitor
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
from classiq.interface.model.port_declaration import AnonPortDeclaration
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
    AnonPositionalArg,
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

import classiq
from classiq.qmod.builtins.functions import BUILTIN_FUNCTION_DECLARATIONS
from classiq.qmod.pretty_print.expression_to_python import transform_expression


class VariableDeclarationAssignment(Visitor):
    # FIXME: Support classical variable types

    def __init__(self, pretty_printer: "PythonPrettyPrinter") -> None:
        self.pretty_printer = pretty_printer

    def visit(self, node: NodeType) -> tuple[str, list[str]]:
        res = super().visit(node)
        if not isinstance(res, tuple):
            raise AssertionError(f"Pretty printing for {type(node)} is not supported ")
        return res  # type: ignore[return-value]

    def visit_QuantumBit(self, qtype: QuantumBit) -> tuple[str, list[str]]:
        self.pretty_printer._imports["QBit"] = 1
        return "QBit", []

    def visit_QuantumBitvector(
        self, qtype: QuantumBitvector
    ) -> tuple[str, Optional[list[str]]]:
        self.pretty_printer._imports["QArray"] = 1

        element_type = self.pretty_printer.visit(qtype.element_type)
        if qtype.length is not None:
            return "QArray", [element_type, self.pretty_printer.visit(qtype.length)]
        return "QArray", [element_type]

    def visit_QuantumNumeric(
        self, qtype: QuantumNumeric
    ) -> tuple[str, Optional[list[str]]]:
        self.pretty_printer._imports["QNum"] = 1
        return "QNum", self.pretty_printer._get_qnum_properties(qtype)

    def visit_TypeName(self, qtype: TypeName) -> tuple[str, list[str]]:
        return qtype.name, []


class PythonPrettyPrinter(ModelVisitor):
    def __init__(self, decimal_precision: int = DEFAULT_DECIMAL_PRECISION) -> None:
        self._level = 0
        self._decimal_precision = decimal_precision
        self._imports = {"qfunc": 1}
        self._import_enum = False
        self._import_dataclass = False
        self._import_annotated = False
        self._symbolic_imports: dict[str, int] = dict()
        self._functions: Optional[Mapping[str, QuantumFunctionDeclaration]] = None
        self._compilation_metadata: dict[str, CompilationMetadata] = dict()

    def visit(self, node: NodeType) -> str:
        res = super().visit(node)
        if not isinstance(res, str):
            raise AssertionError(f"Pretty printing for {type(node)} is not supported ")
        return res

    def visit_Model(self, model: Model) -> str:
        self._functions = {**model.function_dict, **BUILTIN_FUNCTION_DECLARATIONS}
        self._compilation_metadata = model.functions_compilation_metadata
        enum_decls = [self.visit(decl) for decl in model.enums]
        struct_decls = [self.visit(decl) for decl in model.types]
        qstruct_decls = [self.visit(qstruct_decl) for qstruct_decl in model.qstructs]
        func_defs = [self.visit(func) for func in model.functions]
        constants = [self.visit(const) for const in model.constants]
        classical_code = self.format_classical_code(model.classical_execution_code)

        code = f"{self.format_imports()}\n\n{self.join_code_parts(*constants, *enum_decls, *struct_decls, *qstruct_decls, *func_defs, classical_code)}"
        return black.format_str(code, mode=black.FileMode())

    def format_classical_code(self, code: str) -> str:
        if not code:
            return ""
        self._imports["cfunc"] = 1
        self.check_execution_primitives(code)
        formatted_code = code.replace("\n", "\n" + self._indent + "    ")
        return f"{self._indent}@cfunc\n{self._indent}def cmain() -> None:\n{self._indent}    {formatted_code}"

    def check_execution_primitives(self, code: str) -> None:
        for primitive in dir(classiq.qmod.builtins.classical_execution_primitives):
            if primitive + "(" in code:
                self._imports[primitive] = 1

    def format_imports(self) -> str:
        imports = f"from classiq import {', '.join(self._imports.keys())}\n"
        symbolic_imports = (
            f"from classiq.qmod.symbolic import {', '.join(self._symbolic_imports.keys())}\n"
            if self._symbolic_imports
            else ""
        )
        return self.special_imports + imports + symbolic_imports

    @property
    def special_imports(self) -> str:
        imports = ""
        if self._import_annotated:
            imports += "from typing import Annotated\n"
        if self._import_dataclass:
            imports += "from dataclasses import dataclass\n"
        if self._import_enum:
            imports += "from enum import IntEnum\n"
        return imports

    def join_code_parts(self, *code_parts: str) -> str:
        return "\n".join(code_parts)

    def visit_Constant(self, constant: Constant) -> str:
        self._imports["QConstant"] = 1
        constant_name = self.visit(constant.name)
        return f'{self._indent}{constant_name} = QConstant("{constant_name}", {self.visit(constant.const_type)}, {self.visit(constant.value)})\n'

    def _visit_arg_decls(self, func_def: QuantumFunctionDeclaration) -> str:
        return ", ".join(
            self.visit(arg_decl) for arg_decl in func_def.positional_arg_declarations
        )

    def _get_qfunc_decorator(self, func_decl: QuantumFunctionDeclaration) -> str:
        no_unchecked_decorator = "@qfunc"
        if func_decl.name not in self._compilation_metadata:
            return no_unchecked_decorator
        unchecked = self._compilation_metadata[func_decl.name].unchecked
        if len(unchecked) == 0:
            return no_unchecked_decorator

        unchecked_modifiers = (f'"{modifier}"' for modifier in unchecked)
        unchecked_list = f"[{', '.join(unchecked_modifiers)}]"
        return no_unchecked_decorator + f" (unchecked={unchecked_list})"

    def visit_QuantumFunctionDeclaration(
        self, func_decl: QuantumFunctionDeclaration
    ) -> str:
        qfunc_decorator = self._get_qfunc_decorator(func_decl)
        return f"{qfunc_decorator}\ndef {func_decl.name}({self._visit_arg_decls(func_decl)}) -> None:"

    def visit_EnumDeclaration(self, enum_decl: EnumDeclaration) -> str:
        self._import_enum = True
        return f"class {enum_decl.name}(IntEnum):\n{self._visit_members(enum_decl.members)}\n"

    def _visit_members(self, members: dict[str, int]) -> str:
        self._level += 1
        members_str = "".join(
            f"{self._indent}{self.visit(member_name)} = {member_value}\n"
            for member_name, member_value in members.items()
        )
        self._level -= 1
        return members_str

    def visit_StructDeclaration(self, struct_decl: StructDeclaration) -> str:
        self._import_dataclass = True
        return f"@dataclass\nclass {struct_decl.name}:\n{self._visit_variables(struct_decl.variables)}\n"

    def visit_QStructDeclaration(self, qstruct_decl: QStructDeclaration) -> str:
        self._imports["QStruct"] = 1
        return f"class {qstruct_decl.name}(QStruct):\n{self._visit_variables(qstruct_decl.fields)}\n"

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
        var_type = self._extract_port_type(port_decl)
        return f"{port_decl.name}: {var_type}"

    def _extract_port_type(self, port_decl: AnonPortDeclaration) -> str:
        var_type = self.visit(port_decl.quantum_type)
        if port_decl.direction is not PortDeclarationDirection.Inout:
            self._imports[port_decl.direction.name] = 1
            var_type = f"{port_decl.direction.name}[{var_type}]"
        if port_decl.type_modifier in [TypeModifier.Const, TypeModifier.Permutable]:
            self._imports[port_decl.type_modifier.name] = 1
            var_type = f"{port_decl.type_modifier.name}[{var_type}]"
        return var_type

    def visit_QuantumBit(self, qtype: QuantumBit) -> str:
        self._imports["QBit"] = 1
        return "QBit"

    def visit_QuantumBitvector(self, qtype: QuantumBitvector) -> str:
        self._imports.update({"QArray": 1, "QBit": 1})
        element_type = self.visit(qtype.element_type)
        if qtype.length is not None:
            return f"QArray[{element_type}, {_add_quotes(self.visit(qtype.length))}]"
        return f"QArray[{element_type}]"

    def visit_QuantumNumeric(self, qtype: QuantumNumeric) -> str:
        self._imports["QNum"] = 1
        params = ""
        qnum_properties = self._get_qnum_properties(qtype)
        if len(qnum_properties) > 0:
            params = "[{}]".format(
                ", ".join(_add_quotes(param) for param in qnum_properties)
            )
        return f"QNum{params}"

    def _get_qnum_properties(self, qtype: QuantumNumeric) -> list[str]:
        params: list[str] = []
        if qtype.size is None:
            return params
        params.append(self.visit(qtype.size))

        is_signed_expr = qtype.is_signed
        fraction_digits_expr = qtype.fraction_digits
        if is_signed_expr is None:
            if fraction_digits_expr is not None:
                raise ClassiqInternalError
            return params
        if fraction_digits_expr is None:
            raise ClassiqInternalError

        is_unsigned = (
            is_signed_expr.is_evaluated() and not is_signed_expr.to_bool_value()
        ) or is_signed_expr.expr == "UNSIGNED"
        is_integer = (
            fraction_digits_expr.is_evaluated()
            and fraction_digits_expr.to_int_value() == 0
        )
        if is_unsigned and is_integer:
            return params
        params.append(self.visit(is_signed_expr))
        params.append(self.visit(fraction_digits_expr))

        return params

    def visit_AnonClassicalParameterDeclaration(
        self, cparam: AnonClassicalParameterDeclaration
    ) -> str:
        return f"{cparam.name}: {self.visit(cparam.classical_type)}"

    def visit_Integer(self, ctint: Integer) -> str:
        self._imports["CInt"] = 1
        return "CInt"

    def visit_Real(self, ctint: Real) -> str:
        self._imports["CReal"] = 1
        return "CReal"

    def visit_Bool(self, ctbool: Bool) -> str:
        self._imports["CBool"] = 1
        return "CBool"

    def visit_ClassicalArray(self, ctarray: ClassicalArray) -> str:
        self._imports["CArray"] = 1
        element_type = self.visit(ctarray.element_type)
        if ctarray.length is not None:
            return f"CArray[{element_type}, {_add_quotes(self.visit(ctarray.length))}]"
        return f"CArray[{element_type}]"

    def visit_ClassicalTuple(self, classical_tuple: ClassicalTuple) -> str:
        raw_type = classical_tuple.get_raw_type()
        if isinstance(raw_type, ClassicalTuple):
            raise ClassiqInternalError("Empty tuple pretty-print not supported")
        return self.visit(raw_type)

    def visit_TypeName(self, type_: TypeName) -> str:
        self._import_type_name(type_)
        return type_.name

    def _import_type_name(self, type_: TypeName) -> None:
        if type_.name in dir(classiq.qmod.builtins.enums) + dir(
            classiq.qmod.builtins.structs
        ):
            self._imports[type_.name] = 1

    def visit_VariableDeclarationStatement(
        self,
        local_decl: VariableDeclarationStatement,
        walrus: bool = False,
    ) -> str:
        type_name, params = VariableDeclarationAssignment(self).visit(
            local_decl.qmod_type
        )
        params = [f'"{local_decl.name}"'] + params
        param_args = ", ".join(params)

        res = f"{self._indent}{local_decl.name}"
        if walrus:
            res += " := "
        else:
            res += f": {self.visit(local_decl.qmod_type)} = "
        res += f"{type_name}({param_args})\n"
        return res

    def _visit_operand_arg_decl(self, arg_decl: AnonPositionalArg) -> str:
        if isinstance(arg_decl, AnonPortDeclaration):
            type_str = self._extract_port_type(arg_decl)
        elif isinstance(arg_decl, AnonClassicalParameterDeclaration):
            type_str = self.visit(arg_decl.classical_type)
        else:
            type_str = self.visit_AnonQuantumOperandDeclaration(arg_decl, no_param=True)
        if arg_decl.name is None:
            return type_str
        self._import_annotated = True
        return f'Annotated[{type_str}, "{arg_decl.name}"]'

    def visit_AnonQuantumOperandDeclaration(
        self, op_decl: AnonQuantumOperandDeclaration, no_param: bool = False
    ) -> str:
        qcallable_identifier = "QCallableList" if op_decl.is_list else "QCallable"
        self._imports[qcallable_identifier] = 1
        args = ", ".join(
            self._visit_operand_arg_decl(arg_decl)
            for arg_decl in op_decl.positional_arg_declarations
        )
        param_name = "" if no_param else f"{op_decl.name}: "
        return f"{param_name}{qcallable_identifier}" + (f"[{args}]" if args else "")

    def visit_QuantumOperandDeclaration(
        self, op_decl: QuantumOperandDeclaration
    ) -> str:
        return self.visit_AnonQuantumOperandDeclaration(op_decl)

    def visit_NativeFunctionDefinition(self, func_def: NativeFunctionDefinition) -> str:
        self._level += 1
        if len(func_def.body) == 0:
            body = "    pass"
        else:
            body = "".join(self.visit(statement) for statement in func_def.body)
        self._level -= 1
        return f"{self.visit_QuantumFunctionDeclaration(func_def)} \n{body}\n"

    def visit_QuantumFunctionCall(self, func_call: QuantumFunctionCall) -> str:
        args = self._get_args(func_call)
        if func_call.func_name in dir(classiq.qmod.builtins.functions):
            self._imports[func_call.func_name] = 1
        return f"{self._indent}{func_call.func_name}{f'[{self.visit(func_call.function.index)}]' if isinstance(func_call.function, OperandIdentifier) else ''}({args})\n"

    def _get_args(self, func_call: QuantumFunctionCall) -> str:
        if len(func_call.positional_args) > 2 and self._functions is not None:
            func_decl = self._functions[func_call.func_name]
            if all(
                param.name is not None
                for param in func_decl.positional_arg_declarations
            ):
                return ", ".join(
                    f"{self.visit(cast(str, arg_decl.name))}={self.visit(arg)}"
                    for arg_decl, arg in zip(
                        func_decl.positional_arg_declarations,
                        func_call.positional_args,
                    )
                )
        return ", ".join(self.visit(arg) for arg in func_call.positional_args)

    def visit_Allocate(self, allocate: Allocate) -> str:
        self._imports["allocate"] = 1
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
        return f"{self._indent}allocate({params})\n"

    def visit_Control(self, op: Control) -> str:
        self._imports["control"] = 1
        control_else = (
            f", {self._visit_body(op.else_block)}" if op.else_block is not None else ""
        )
        return f"{self._indent}control({self.visit(op.expression)}, {self._visit_body(op.body)}{control_else})\n"

    def visit_PhaseOperation(self, op: PhaseOperation) -> str:
        self._imports["phase"] = 1
        theta = f", {self.visit(op.theta)}" if op.theta is not None else ""
        return f"{self._indent}phase({self.visit(op.expression)}{theta})\n"

    def visit_ClassicalIf(self, op: ClassicalIf) -> str:
        self._imports["if_"] = 1
        return f"{self._indent}if_(condition={self.visit(op.condition)}, then={self._visit_body(op.then)}, else_={self._visit_body(op.else_)})\n"

    def visit_WithinApply(self, op: WithinApply) -> str:
        self._imports["within_apply"] = 1
        return f"{self._indent}within_apply({self._visit_body(op.compute)}, {self._visit_body(op.action)})\n"

    def visit_Repeat(self, repeat: Repeat) -> str:
        self._imports["repeat"] = 1
        return f"{self._indent}repeat({self.visit(repeat.count)}, {self._visit_body(repeat.body, [repeat.iter_var])})\n"

    def visit_Power(self, power: Power) -> str:
        self._imports["power"] = 1
        return f"{self._indent}power({self.visit(power.power)}, {self._visit_body(power.body)})\n"

    def visit_Invert(self, invert: Invert) -> str:
        self._imports["invert"] = 1
        return f"{self._indent}invert({self._visit_body(invert.body)})\n"

    def visit_Block(self, block: Block) -> str:
        self._imports["block"] = 1
        return f"{self._indent}block({self._visit_body(block.statements)})\n"

    def _visit_body(
        self, body: StatementBlock, operand_arguments: Optional[list[str]] = None
    ) -> str:
        if len(body) == 0:
            return "lambda: []"
        argument_string = (
            (" " + ", ".join(operand_arguments)) if operand_arguments else ""
        )
        code = f"lambda{argument_string}: {'[' if len(body) > 1 else ''}\n"
        self._level += 1
        for i, statement in enumerate(body):
            if isinstance(statement, VariableDeclarationStatement):
                code += self.visit_VariableDeclarationStatement(statement, walrus=True)
            elif isinstance(statement, AmplitudeLoadingOperation):
                code += self.visit_AmplitudeLoadingOperation(statement, in_lambda=True)
            elif isinstance(statement, ArithmeticOperation):
                code += self.visit_ArithmeticOperation(statement, in_lambda=True)
            else:
                code += self.visit(statement)
            if i < len(body) - 1:
                code += ","
        self._level -= 1
        return f"{code}{']' if len(body) > 1 else ''}"

    def visit_InplaceBinaryOperation(self, op: InplaceBinaryOperation) -> str:
        self._imports[op.operation.value] = 1
        return f"{self._indent}{op.operation.value}({self.visit(op.value)}, {self.visit(op.target)})\n"

    def visit_Expression(self, expr: Expression) -> str:
        return transform_expression(
            expr.expr,
            level=self._level,
            decimal_precision=self._decimal_precision,
            imports=self._imports,
            symbolic_imports=self._symbolic_imports,
        )

    def visit_QuantumLambdaFunction(self, qlambda: QuantumLambdaFunction) -> str:
        return self._visit_body(qlambda.body, qlambda.pos_rename_params)

    def visit_HandleBinding(self, var_ref: HandleBinding) -> str:
        return var_ref.name

    def visit_SlicedHandleBinding(self, var_ref: SlicedHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}[{self.visit(var_ref.start)}:{self.visit(var_ref.end)}]"

    def visit_SubscriptHandleBinding(self, var_ref: SubscriptHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}[{self.visit(var_ref.index)}]"

    def visit_FieldHandleBinding(self, var_ref: FieldHandleBinding) -> str:
        return f"{self.visit(var_ref.base_handle)}.{self.visit(var_ref.field)}"

    def visit_HandlesList(self, handles: HandlesList) -> str:
        return self.visit(handles.handles)

    def visit_ArithmeticOperation(
        self, arith_op: ArithmeticOperation, in_lambda: bool = False
    ) -> str:
        if arith_op.operation_kind == ArithmeticOperationKind.Assignment:
            op = "|="
            func = "assign"
        elif arith_op.operation_kind == ArithmeticOperationKind.InplaceXor:
            op = "^="
            func = "inplace_xor"
        else:
            op = "+="
            func = "inplace_add"
        if in_lambda:
            self._imports[func] = 1
            return f"{func}({self.visit(arith_op.expression)}, {self._indent}{self.visit(arith_op.result_var)})\n"
        return f"{self._indent}{self.visit(arith_op.result_var)} {op} {self.visit(arith_op.expression)}\n"

    def visit_AmplitudeLoadingOperation(
        self, amplitude_loading_op: AmplitudeLoadingOperation, in_lambda: bool = False
    ) -> str:
        if in_lambda:
            self._imports["assign_amplitude"] = 1
            return f"assign_amplitude({self.visit(amplitude_loading_op.expression)}, {self._indent}{self.visit(amplitude_loading_op.result_var)})\n"
        return f"{self._indent}{self.visit(amplitude_loading_op.result_var)} *= {self.visit(amplitude_loading_op.expression)}\n"

    def _print_bind_handles(self, handles: list[HandleBinding]) -> str:
        if len(handles) == 1:
            return self.visit(handles[0])

        return "[" + ", ".join(self.visit(handle) for handle in handles) + "]"

    def visit_BindOperation(self, bind_op: BindOperation) -> str:
        self._imports["bind"] = 1
        return f"{self._indent}bind({self._print_bind_handles(bind_op.in_handles)}, {self._print_bind_handles(bind_op.out_handles)})\n"

    def visit_list(self, node: list) -> str:
        return "[" + ", ".join(self.visit(elem) for elem in node) + "]"

    def visit_OperandIdentifier(self, op: OperandIdentifier) -> str:
        return str(op)

    def visit_SetBoundsStatement(self, op: SetBoundsStatement) -> str:
        self._imports["reset_bounds"] = 1
        target = self.visit(op.target)
        if op.lower_bound is None or op.upper_bound is None:
            return f"{self._indent}reset_bounds({target})\n"
        else:
            lower_bound = self.visit(op.lower_bound)
            upper_bound = self.visit(op.upper_bound)
            return (
                f"{self._indent}reset_bounds({target}, {lower_bound}, {upper_bound})\n"
            )

    @property
    def _indent(self) -> str:
        return "    " * self._level


def _add_quotes(exp: str) -> str:
    if (
        exp.lower() == "true"
        or exp.lower() == "false"
        or _convertible_to_number(exp)
        or _is_constant(exp)
    ):
        return exp

    return f'"{exp}"'


def _convertible_to_number(exp: str) -> bool:
    for number_type in [int, float]:
        try:
            number_type(exp)
        except ValueError:
            pass
        else:
            return True
    return False


def _is_constant(exp: str) -> bool:
    return exp in ("SIGNED", "UNSIGNED")
