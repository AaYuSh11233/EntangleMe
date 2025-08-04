import ast
from typing import cast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.type_name import Struct
from classiq.interface.generator.types.struct_declaration import StructDeclaration
from classiq.interface.helpers.text_utils import readable_list, s

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.compare_evaluation import (
    comparison_allowed,
)


def eval_struct_instantiation(
    expr_val: QmodAnnotatedExpression, node: ast.Call, decl: StructDeclaration
) -> None:
    if len(node.args) > 0 or any(kwarg.arg is None for kwarg in node.keywords):
        raise ClassiqExpansionError(
            "Classical structs must be instantiated using keyword arguments"
        )

    field_assignments = {cast(str, kwarg.arg): kwarg.value for kwarg in node.keywords}
    assigned_fields = list(field_assignments)
    expected_fields = list(decl.variables)
    if set(assigned_fields) != set(expected_fields):
        raise ClassiqExpansionError(
            f"Struct {decl.name} has field{s(expected_fields)} "
            f"{readable_list(expected_fields, quote=True)} but was instantiated "
            f"using the field{s(assigned_fields)} "
            f"{readable_list(assigned_fields, quote=True)}"
        )

    for field_name, field_value in field_assignments.items():
        assignment_type = expr_val.get_type(field_value)
        expected_type = decl.variables[field_name]
        if not comparison_allowed(assignment_type, expected_type):
            raise ClassiqExpansionError(
                f"Cannot assign value of type {assignment_type.qmod_type_name} "
                f"to field {field_name!r} of type {expected_type.qmod_type_name}"
            )

    classical_type = Struct(name=decl.name)
    classical_type.set_classical_struct_decl(decl)
    expr_val.set_type(node, classical_type)

    if any(
        not expr_val.has_value(field_value)
        for field_value in field_assignments.values()
    ):
        return

    struct_val = QmodStructInstance(
        decl,
        {
            field_name: expr_val.get_value(field_value)
            for field_name, field_value in field_assignments.items()
        },
    )
    expr_val.set_value(node, struct_val)
