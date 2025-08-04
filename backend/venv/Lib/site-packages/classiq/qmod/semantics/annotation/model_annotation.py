from classiq.interface.model.model import Model

from classiq.qmod.semantics.annotation.call_annotation import resolve_function_calls
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator


def annotate_model(model: Model) -> None:
    QStructAnnotator().visit(model)
    resolve_function_calls(model)
