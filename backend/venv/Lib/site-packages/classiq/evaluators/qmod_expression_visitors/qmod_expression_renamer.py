from classiq.interface.model.handle_binding import HandleBinding

from classiq.evaluators.qmod_annotated_expression import (
    QmodAnnotatedExpression,
    QmodExprNodeId,
)


def replace_expression_vars(
    expr_val: QmodAnnotatedExpression,
    renaming: dict[HandleBinding, HandleBinding],
) -> None:
    if len(renaming) == 0:
        return
    all_vars = expr_val.get_classical_vars() | expr_val.get_quantum_vars()
    for node_id, var in all_vars.items():
        renamed_var = var
        for source, target in renaming.items():
            if renamed_var.name == source.name:
                renamed_var = renamed_var.replace_prefix(source, target)
        if renamed_var is var:
            continue
        node_type = expr_val.get_type(node_id)
        expr_val.clear_node_data(node_id)
        expr_val.set_type(node_id, node_type)
        expr_val.set_var(node_id, renamed_var)
    return


def replace_expression_type_attrs(
    expr_val: QmodAnnotatedExpression,
    renaming: dict[tuple[HandleBinding, str], HandleBinding],
) -> None:
    if len(renaming) == 0:
        return
    type_attrs = dict(expr_val.get_quantum_type_attributes())
    for node_id, ta in type_attrs.items():
        var = expr_val.get_var(ta.value)
        renamed_var = var
        renamed_attr = ta.attr
        for (source, attr), target in renaming.items():
            if renamed_attr == attr and renamed_var.name == source.name:
                renamed_var = renamed_var.replace_prefix(source, target)
        if renamed_var is var:
            continue
        node_type = expr_val.get_type(node_id)
        expr_val.clear_node_data(node_id)
        expr_val.set_type(node_id, node_type)
        expr_val.set_var(node_id, renamed_var)
    return


def replace_expression_nodes(
    expr_val: QmodAnnotatedExpression,
    renaming: dict[QmodExprNodeId, str],
) -> str:
    for node_id, renamed_var in renaming.items():
        expr_val.set_var(node_id, HandleBinding(name=f"{renamed_var}"))
    return str(expr_val)
