from typing import Any, Callable, Optional, Union, overload

from classiq.qmod.classical_function import CFunc


def get_caller_locals() -> dict[str, Any]:
    """Print the local variables in the caller's frame."""
    import inspect

    frame = inspect.currentframe()
    try:
        assert frame is not None
        cfunc_frame = frame.f_back
        assert cfunc_frame is not None
        caller_frame = cfunc_frame.f_back
        assert caller_frame is not None

        return caller_frame.f_locals
    finally:
        # See here for information about the `del`
        # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
        del frame


@overload
def cfunc(func: Callable) -> CFunc: ...


@overload
def cfunc(func: None = None) -> Callable[[Callable], CFunc]: ...


def cfunc(func: Optional[Callable] = None) -> Union[Callable[[Callable], CFunc], CFunc]:
    caller_locals = get_caller_locals()

    def wrapper(func: Callable) -> CFunc:
        return CFunc(func, caller_locals)

    if func is not None:
        return wrapper(func)

    return wrapper
