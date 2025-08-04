from collections.abc import Sequence
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
)

import pydantic
from pydantic import SerializeAsAny
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Self

from classiq.interface.exceptions import ClassiqInternalError
from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import ArithmeticIODict, PortDirection
from classiq.interface.generator.functions.function_declaration import (
    FunctionDeclaration,
)
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.helpers.pydantic_model_helpers import (
    values_with_discriminator,
)
from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
    ClassicalParameterDeclaration,
)
from classiq.interface.model.port_declaration import (
    AnonPortDeclaration,
    PortDeclaration,
)
from classiq.interface.model.quantum_type import quantum_var_to_register

AnonPositionalArg = Annotated[
    Union[
        AnonClassicalParameterDeclaration,
        "AnonQuantumOperandDeclaration",
        AnonPortDeclaration,
    ],
    pydantic.Field(..., discriminator="kind"),
]


def _ports_to_registers(
    port_declarations: Sequence[AnonPortDeclaration], direction: PortDirection
) -> Sequence[RegisterUserInput]:
    return [
        quantum_var_to_register(port_decl.get_name(), port_decl.quantum_type)
        for port_decl in port_declarations
        if port_decl.direction.includes_port_direction(direction)
    ]


class AnonQuantumFunctionDeclaration(FunctionDeclaration):
    """
    Facilitates the creation of a common quantum function interface object.
    """

    positional_arg_declarations: Sequence[AnonPositionalArg] = pydantic.Field(
        default_factory=list
    )

    @property
    def port_declarations(self) -> Sequence[AnonPortDeclaration]:
        return [
            arg
            for arg in self.positional_arg_declarations
            if isinstance(arg, AnonPortDeclaration)
        ]

    @property
    def operand_declarations(self) -> Sequence["AnonQuantumOperandDeclaration"]:
        return [
            arg
            for arg in self.positional_arg_declarations
            if isinstance(arg, AnonQuantumOperandDeclaration)
        ]

    @property
    def param_decls(self) -> Sequence[AnonClassicalParameterDeclaration]:
        return [
            arg
            for arg in self.positional_arg_declarations
            if isinstance(arg, AnonClassicalParameterDeclaration)
        ]

    @property
    def param_names(self) -> list[str]:
        return [param.get_name() for param in self.param_decls]

    @property
    def input_set(self) -> set[str]:
        return {inp.name for inp in self.inputs}

    @property
    def output_set(self) -> set[str]:
        return {output.name for output in self.outputs}

    @property
    def inputs(self) -> Sequence[RegisterUserInput]:
        return _ports_to_registers(self.port_declarations, PortDirection.Input)

    @property
    def outputs(self) -> Sequence[RegisterUserInput]:
        return _ports_to_registers(self.port_declarations, PortDirection.Output)

    @property
    def port_names(self) -> Sequence[str]:
        return [port.get_name() for port in self.port_declarations]

    @property
    def operand_names(self) -> Sequence[str]:
        return [operand.get_name() for operand in self.operand_declarations]

    def ports_by_direction(
        self, direction: PortDirection
    ) -> Sequence[AnonPortDeclaration]:
        return [
            port
            for port in self.port_declarations
            if port.direction.includes_port_direction(direction)
        ]

    def ports_by_declaration_direction(
        self, direction: PortDeclarationDirection
    ) -> set[str]:
        return {
            port.get_name()
            for port in self.port_declarations
            if port.direction == direction
        }

    def rename(self, new_name: str) -> "QuantumFunctionDeclaration":
        if type(self) not in (
            AnonQuantumFunctionDeclaration,
            QuantumFunctionDeclaration,
            NamedParamsQuantumFunctionDeclaration,
        ):
            raise ClassiqInternalError
        return QuantumFunctionDeclaration(
            **{
                **{
                    field_name: field_value
                    for field_name, field_value in self.__dict__.items()
                    if field_name in AnonQuantumFunctionDeclaration.model_fields
                },
                "name": new_name,
            }
        )


class AnonQuantumOperandDeclaration(AnonQuantumFunctionDeclaration):
    kind: Literal["QuantumOperandDeclaration"]

    is_list: bool = pydantic.Field(
        description="Indicate whether the operand expects an unnamed list of lambdas",
        default=False,
    )
    _is_generative: bool = pydantic.PrivateAttr(default=False)

    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_kind(cls, values: Any) -> dict[str, Any]:
        return values_with_discriminator(values, "kind", "QuantumOperandDeclaration")

    def rename(self, new_name: str) -> "QuantumOperandDeclaration":
        if type(self) not in (AnonQuantumOperandDeclaration, QuantumOperandDeclaration):
            raise ClassiqInternalError
        new_instance_data = self.__dict__.copy()
        new_instance_data["name"] = new_name
        new_instance_data["kind"] = "QuantumOperandDeclaration"
        new_decl = QuantumOperandDeclaration(**new_instance_data)
        if self._is_generative:
            new_decl.set_generative()
        return new_decl

    @property
    def element_declaration(self) -> Self:
        if not self.is_list:
            raise ClassiqInternalError
        return self.model_copy(update={"is_list": False})

    def set_generative(self) -> Self:
        self._is_generative = True
        return self

    @property
    def is_generative(self) -> bool:
        return self._is_generative


AnonQuantumFunctionDeclaration.model_rebuild()


class QuantumFunctionDeclaration(AnonQuantumFunctionDeclaration):
    name: str


class QuantumOperandDeclaration(
    AnonQuantumOperandDeclaration, QuantumFunctionDeclaration
):
    @pydantic.model_validator(mode="before")
    @classmethod
    def _set_none(cls, values: Any, info: ValidationInfo) -> dict[str, Any]:
        return values


PositionalArg = Annotated[
    SerializeAsAny[
        Union[
            ClassicalParameterDeclaration,
            QuantumOperandDeclaration,
            PortDeclaration,
        ]
    ],
    pydantic.Field(..., discriminator="kind"),
]


class NamedParamsQuantumFunctionDeclaration(QuantumFunctionDeclaration):

    positional_arg_declarations: Sequence[PositionalArg] = pydantic.Field(
        default_factory=list
    )

    @property
    def port_declarations_dict(self) -> dict[str, PortDeclaration]:
        return {port.name: port for port in self.port_declarations}

    @property
    def operand_declarations_dict(self) -> dict[str, QuantumOperandDeclaration]:
        return {op.name: op for op in self.operand_declarations}

    @property
    def param_decls_dict(self) -> dict[str, ClassicalParameterDeclaration]:
        return {param.name: param for param in self.param_decls}

    @property
    def inputs_dict(self) -> ArithmeticIODict:
        return _ports_to_registers_dict(self.port_declarations, PortDirection.Input)

    @property
    def inouts_dict(self) -> ArithmeticIODict:
        return _ports_to_registers_dict(self.port_declarations, PortDirection.Inout)

    @property
    def outputs_dict(self) -> ArithmeticIODict:
        return _ports_to_registers_dict(self.port_declarations, PortDirection.Output)

    @property
    def port_declarations(self) -> Sequence[PortDeclaration]:
        return super().port_declarations  # type:ignore[return-value]

    @property
    def operand_declarations(self) -> Sequence[QuantumOperandDeclaration]:
        return super().operand_declarations  # type:ignore[return-value]

    @property
    def param_decls(self) -> Sequence[ClassicalParameterDeclaration]:
        return super().param_decls  # type:ignore[return-value]


def _ports_to_registers_dict(
    port_declarations: Sequence[PortDeclaration], direction: PortDirection
) -> ArithmeticIODict:
    return {
        port_decl.name: quantum_var_to_register(port_decl.name, port_decl.quantum_type)
        for port_decl in port_declarations
        if port_decl.direction.includes_port_direction(direction)
    }
