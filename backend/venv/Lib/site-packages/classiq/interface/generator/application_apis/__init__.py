from classiq.interface.generator.builtin_api_builder import (
    populate_builtin_declarations,
)

from .arithmetic_declarations import *  # noqa: F403
from .chemistry_declarations import *  # noqa: F403
from .combinatorial_optimization_declarations import *  # noqa: F403
from .entangler_declarations import *  # noqa: F403
from .finance_declarations import *  # noqa: F403
from .qsvm_declarations import *  # noqa: F403

populate_builtin_declarations(vars().values())
