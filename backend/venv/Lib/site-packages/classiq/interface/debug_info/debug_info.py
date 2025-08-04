from collections.abc import Mapping, Sequence
from typing import Optional, Union, cast
from uuid import UUID

from pydantic import BaseModel, Field

from classiq.interface.debug_info import back_ref_util
from classiq.interface.generator.generated_circuit_data import (
    FunctionDebugInfoInterface,
    StatementType,
)
from classiq.interface.model.handle_binding import ConcreteHandleBinding
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_call import ArgValue
from classiq.interface.model.quantum_function_declaration import PositionalArg
from classiq.interface.model.statement_block import ConcreteQuantumStatement

ParameterValue = Union[float, int, str, None]


class FunctionDebugInfo(BaseModel):
    name: str
    statement_type: Union[StatementType, None] = None
    is_inverse: bool = Field(default=False)
    control_variable: Optional[str] = Field(default=None)
    port_to_passed_variable_map: dict[str, str] = Field(default_factory=dict)
    node: Optional[ConcreteQuantumStatement] = None

    @property
    def is_allocate_or_free(self) -> bool:
        return back_ref_util.is_allocate_or_free(self.node) if self.node else False

    def update_map_from_port_mapping(self, port_mapping: Mapping[str, str]) -> None:
        new_port_to_passed_variable_map = self.port_to_passed_variable_map.copy()
        for old_key, new_key in port_mapping.items():
            if old_key in new_port_to_passed_variable_map:
                new_port_to_passed_variable_map[new_key] = (
                    new_port_to_passed_variable_map.pop(old_key)
                )
        self.port_to_passed_variable_map = new_port_to_passed_variable_map

    def update_map_from_inout_port_mapping(
        self, port_mapping: Mapping[str, tuple[str, str]]
    ) -> None:
        new_port_to_passed_variable_map = self.port_to_passed_variable_map.copy()
        for old_key, (new_key1, new_key2) in port_mapping.items():
            if old_key in new_port_to_passed_variable_map:
                value = new_port_to_passed_variable_map.pop(old_key)
                new_port_to_passed_variable_map[new_key1] = value
                new_port_to_passed_variable_map[new_key2] = value
        self.port_to_passed_variable_map = new_port_to_passed_variable_map


class DebugInfoCollection(BaseModel):
    # Pydantic only started supporting UUID as keys in Pydantic V2
    # See https://github.com/pydantic/pydantic/issues/2096#issuecomment-814860206
    # For now, we use strings as keys in the raw data and use UUID in the wrapper logic
    data: dict[str, FunctionDebugInfo] = Field(default={})
    blackbox_data: dict[str, FunctionDebugInfoInterface] = Field(default={})

    def __setitem__(self, key: UUID, value: FunctionDebugInfo) -> None:
        self.data[str(key)] = value

    def get(self, key: UUID) -> Optional[FunctionDebugInfo]:
        return self.data.get(str(key))

    def __getitem__(self, key: UUID) -> FunctionDebugInfo:
        return self.data[str(key)]

    def __contains__(self, key: UUID) -> bool:
        return str(key) in self.data

    def get_blackbox_data(self, key: UUID) -> Optional[FunctionDebugInfoInterface]:
        if (debug_info := self.get(key)) is None:
            return None
        return self.blackbox_data.get(debug_info.name)


def get_back_refs(
    debug_info: FunctionDebugInfo, collected_debug_info: DebugInfoCollection
) -> list[ConcreteQuantumStatement]:
    back_refs: list[ConcreteQuantumStatement] = []
    while (node := debug_info.node) is not None:
        if len(back_refs) > 0 and node.back_ref == back_refs[0].back_ref:
            break
        back_refs.insert(0, node)
        if node.back_ref is None:
            break
        next_debug_info = collected_debug_info.get(node.back_ref)
        if next_debug_info is None:
            break
        debug_info = next_debug_info
    return back_refs


def new_function_debug_info_by_node(
    node: ConcreteQuantumStatement,
) -> FunctionDebugInfo:
    return FunctionDebugInfo(
        name="",
        node=node._as_back_ref(),
    )


def calculate_port_to_passed_variable_mapping(
    arg_decls: Sequence[PositionalArg], args: Sequence[Union[ArgValue, None]]
) -> dict[str, str]:
    return {
        arg_decl.name: str(cast(ConcreteHandleBinding, arg))
        for arg_decl, arg in zip(arg_decls, args)
        if isinstance(arg_decl, PortDeclaration)
    }
