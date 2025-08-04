from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.model.model import Model

from classiq.qmod.builtins.functions import CORE_LIB_DECLS


def check_function_name_collisions(model: Model) -> None:
    redefined_functions = [
        function.name
        for function in CORE_LIB_DECLS
        if function.name in model.function_dict
    ]
    if len(redefined_functions) == 1:
        raise ClassiqExpansionError(
            f"Cannot redefine built-in function {redefined_functions[0]!r}"
        )
    elif len(redefined_functions) > 1:
        raise ClassiqExpansionError(
            f"Cannot redefine built-in functions: {redefined_functions}"
        )
