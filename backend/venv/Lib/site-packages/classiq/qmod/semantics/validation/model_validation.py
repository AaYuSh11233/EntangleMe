from classiq.interface.model.model import Model

from classiq.qmod.semantics.validation.constants_validation import (
    check_duplicate_constants,
)
from classiq.qmod.semantics.validation.function_name_collisions_validation import (
    check_function_name_collisions,
)
from classiq.qmod.semantics.validation.main_validation import validate_main_function
from classiq.qmod.semantics.validation.types_validation import (
    check_duplicate_types,
    validate_cstruct,
    validate_qstruct,
)


def validate_model(model: Model) -> None:
    check_duplicate_types([*model.enums, *model.types, *model.qstructs])
    check_duplicate_constants(model.constants)
    for qstruct in model.qstructs:
        validate_qstruct(qstruct)
    for cstruct in model.types:
        validate_cstruct(cstruct)
    validate_main_function(model.main_func)
    check_function_name_collisions(model)
