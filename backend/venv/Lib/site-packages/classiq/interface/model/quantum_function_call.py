from collections.abc import Iterable, Mapping, Sequence
from itertools import chain
from typing import (
    Literal,
    Optional,
    Union,
)

import pydantic

from classiq.interface.ast_node import ASTNodeType, reset_lists
from classiq.interface.exceptions import ClassiqError, ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.model.handle_binding import (
    ConcreteHandleBinding,
    GeneralHandle,
    HandleBinding,
    HandlesList,
)
from classiq.interface.model.port_declaration import AnonPortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    QuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_lambda_function import (
    OperandIdentifier,
    QuantumOperand,
)
from classiq.interface.model.quantum_statement import HandleMetadata, QuantumOperation

ArgValue = Union[
    Expression,
    QuantumOperand,
    ConcreteHandleBinding,
    HandlesList,
]


class QuantumFunctionCall(QuantumOperation):
    kind: Literal["QuantumFunctionCall"]

    function: Union[str, OperandIdentifier] = pydantic.Field(
        description="The function that is called"
    )
    positional_args: list[ArgValue] = pydantic.Field(default_factory=list)

    _func_decl: Optional[QuantumFunctionDeclaration] = pydantic.PrivateAttr(
        default=None
    )

    def _as_back_ref(self: ASTNodeType) -> ASTNodeType:
        return reset_lists(self, ["positional_args"])

    @property
    def func_decl(self) -> QuantumFunctionDeclaration:
        if self._func_decl is None:
            raise ClassiqError("Accessing an unresolved quantum function call")

        return self._func_decl

    def set_func_decl(self, fd: Optional[QuantumFunctionDeclaration]) -> None:
        if fd is not None and not isinstance(fd, QuantumFunctionDeclaration):
            raise ClassiqValueError(
                "the declaration of a quantum function call cannot be set to a non-quantum function declaration."
            )
        self._func_decl = fd

    @property
    def func_name(self) -> str:
        if isinstance(self.function, OperandIdentifier):
            return self.function.name
        return self.function

    @property
    def wiring_inputs(self) -> Mapping[str, HandleBinding]:
        return self._get_pos_port_args_by_direction(PortDeclarationDirection.Input)

    @property
    def inputs(self) -> Sequence[HandleBinding]:
        return [
            handle
            for _, _, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Input
            )
        ]

    @property
    def readable_inputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location=self._get_readable_location(param_idx, param),
            )
            for param_idx, param, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Input
            )
        ]

    @property
    def wiring_inouts(
        self,
    ) -> Mapping[str, ConcreteHandleBinding]:
        return self._get_pos_port_args_by_direction(PortDeclarationDirection.Inout)

    @property
    def inouts(self) -> Sequence[HandleBinding]:
        return [
            handle
            for _, _, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Inout
            )
        ]

    @property
    def readable_inouts(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location=self._get_readable_location(param_idx, param),
            )
            for param_idx, param, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Inout
            )
        ]

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return self._get_pos_port_args_by_direction(PortDeclarationDirection.Output)

    @property
    def outputs(self) -> Sequence[HandleBinding]:
        return [
            handle
            for _, _, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Output
            )
        ]

    @property
    def readable_outputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location=self._get_readable_location(param_idx, param),
            )
            for param_idx, param, handle in self._get_handles_by_direction(
                PortDeclarationDirection.Output
            )
        ]

    @property
    def handles_with_directions(
        self,
    ) -> Iterable[tuple[HandleBinding, PortDeclarationDirection]]:
        return [(handle, param.direction) for handle, param in self.handles_with_params]

    @property
    def handles_with_params(
        self,
    ) -> Iterable[tuple[HandleBinding, AnonPortDeclaration]]:
        return [
            (handle, param)
            for arg, param in zip(
                self.positional_args, self.func_decl.positional_arg_declarations
            )
            if isinstance(param, AnonPortDeclaration)
            and isinstance(arg, (HandleBinding, HandlesList))
            for handle in _get_handles(arg)
        ]

    @property
    def params(self) -> list[Expression]:
        return [
            param for param in self.positional_args if isinstance(param, Expression)
        ]

    @property
    def params_dict(self) -> dict[str, Expression]:
        return dict(zip(self.func_decl.param_names, self.params))

    @property
    def operands(self) -> list["QuantumOperand"]:
        return [
            param
            for param in self.positional_args
            if not isinstance(param, (Expression, HandleBinding, HandlesList))
        ]

    @property
    def ports(self) -> list[HandleBinding]:
        return [
            param for param in self.positional_args if isinstance(param, HandleBinding)
        ]

    @property
    def expressions(self) -> list[Expression]:
        return [arg for arg in self.positional_args if isinstance(arg, Expression)]

    def _get_handles_by_direction(
        self, direction: PortDeclarationDirection
    ) -> list[tuple[int, AnonPortDeclaration, HandleBinding]]:
        return [
            (idx, port_decl, handle)
            for idx, port_decl, handle in self._get_handles_with_declarations()
            if direction == port_decl.direction
        ]

    def _get_pos_port_args_by_direction(
        self, direction: PortDeclarationDirection
    ) -> dict[str, HandleBinding]:
        # This is a hack for handles to wires reduction tests,
        # that initialize function definitions or calls not in the scope of a model,
        # so there is no function resolution annotation.
        if self._func_decl is None:
            return dict()
        return {
            port_decl.get_name(): handle
            for _, port_decl, handle in self._get_handles_with_declarations()
            if direction == port_decl.direction
        }

    def _get_handles_with_declarations(
        self,
    ) -> Iterable[tuple[int, AnonPortDeclaration, HandleBinding]]:
        return [
            (idx, port, handle)
            for idx, (port, handle) in enumerate(
                zip(
                    (port_decl for port_decl in self.func_decl.port_declarations),
                    (
                        param
                        for param in self.positional_args
                        if isinstance(param, HandleBinding)
                    ),
                )
            )
        ]

    def _get_readable_location(
        self, param_index: int, param_decl: AnonPortDeclaration
    ) -> str:
        param_name = (
            repr(param_decl.name) if param_decl.name is not None else f"#{param_index}"
        )
        param_text = (
            f" for parameter {param_name}" if len(self.positional_args) > 1 else ""
        )
        return f"as an argument{param_text} of function {self.func_name!r}"


def _get_handles(var: GeneralHandle) -> Iterable[HandleBinding]:
    if isinstance(var, HandleBinding):
        return [var]
    return chain.from_iterable(_get_handles(item) for item in var.handles)
