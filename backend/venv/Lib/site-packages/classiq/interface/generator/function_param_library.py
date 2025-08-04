from collections.abc import Iterable

from classiq.interface.generator.function_params import FunctionParams


class FunctionParamLibrary:
    def __init__(self, param_list: Iterable[type[FunctionParams]]) -> None:
        self._param_list: set[type[FunctionParams]] = set(param_list)

    @property
    def param_list(self) -> set[type[FunctionParams]]:
        return self._param_list.copy()

    # Private methods are for tests only
    def _add(self, param: type[FunctionParams]) -> None:
        self._param_list.add(param)

    def _remove(self, param: type[FunctionParams]) -> None:
        self._param_list.discard(param)
