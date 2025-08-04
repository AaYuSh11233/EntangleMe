from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classiq.interface.generator.types.struct_declaration import StructDeclaration


class TypeProxy:
    def __init__(self, struct_declaration: "StructDeclaration") -> None:
        super().__init__()
        self.struct_declaration = struct_declaration
