from typing import Callable, Literal, Optional, Union, overload

from classiq.interface.exceptions import ClassiqInternalError

from classiq.qmod.global_declarative_switch import get_global_declarative_switch
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.quantum_function import (
    BaseQFunc,
    ExternalQFunc,
    GenerativeQFunc,
    QFunc,
)


@overload
def qfunc(func: Callable) -> GenerativeQFunc: ...


@overload
def qfunc(
    *,
    external: Literal[True],
    synthesize_separately: Literal[False] = False,
    unchecked: Optional[list[str]] = None,
) -> Callable[[Callable], ExternalQFunc]: ...


@overload
def qfunc(
    *,
    generative: Literal[False],
    synthesize_separately: bool = False,
    unchecked: Optional[list[str]] = None,
) -> Callable[[Callable], QFunc]: ...


@overload
def qfunc(
    *, synthesize_separately: bool, unchecked: Optional[list[str]] = None
) -> Callable[[Callable], GenerativeQFunc]: ...


@overload
def qfunc(
    *,
    synthesize_separately: bool = False,
    unchecked: Optional[list[str]] = None,
) -> Callable[[Callable], GenerativeQFunc]: ...


def qfunc(
    func: Optional[Callable] = None,
    *,
    external: bool = False,
    generative: Optional[bool] = None,
    synthesize_separately: bool = False,
    unchecked: Optional[list[str]] = None,
) -> Union[Callable[[Callable], QCallable], QCallable]:
    if generative is None:
        generative = True
    if get_global_declarative_switch():
        generative = False

    def wrapper(func: Callable) -> QCallable:
        qfunc: BaseQFunc

        if external:
            _validate_directives(synthesize_separately, unchecked)
            return ExternalQFunc(func)

        if generative:
            qfunc = GenerativeQFunc(func)
        else:
            qfunc = QFunc(func)
        if synthesize_separately:
            qfunc.update_compilation_metadata(should_synthesize_separately=True)
        if unchecked is not None and len(unchecked) > 0:
            qfunc.update_compilation_metadata(unchecked=unchecked)
        return qfunc

    if func is not None:
        return wrapper(func)
    return wrapper


def _validate_directives(
    synthesize_separately: bool, unchecked: Optional[list[str]] = None
) -> None:
    error_msg = ""
    if synthesize_separately:
        error_msg += "External functions can't be marked as synthesized separately. \n"
    if unchecked is not None and len(unchecked) > 0:
        error_msg += "External functions can't have unchecked modifiers."
    if error_msg:
        raise ClassiqInternalError(error_msg)
