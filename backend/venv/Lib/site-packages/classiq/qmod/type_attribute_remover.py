from classiq.interface.generator.visitor import Transformer
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_declaration import (
    AnonQuantumOperandDeclaration,
)
from classiq.interface.model.quantum_type import QuantumBitvector, QuantumNumeric


def decl_without_type_attributes(
    operand_declaration: AnonQuantumOperandDeclaration,
) -> AnonQuantumOperandDeclaration:
    remover = AttributeRemover()
    return operand_declaration.model_copy(
        update=dict(
            positional_arg_declarations=[
                remover.visit(arg) if isinstance(arg, PortDeclaration) else arg
                for arg in operand_declaration.positional_arg_declarations
            ]
        )
    )


class AttributeRemover(Transformer):
    """Remove attributes that could be expressions such as length, fraction places, etc."""

    def visit_QuantumNumeric(self, node: QuantumNumeric) -> QuantumNumeric:
        return QuantumNumeric(source_ref=node.source_ref)

    def visit_QuantumBitvector(self, node: QuantumBitvector) -> QuantumBitvector:
        return QuantumBitvector(
            element_type=self.visit(node.element_type), source_ref=node.source_ref
        )
