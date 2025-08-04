from collections.abc import Iterator
from contextlib import contextmanager

_DECLARATIVE_SWITCH = False


def get_global_declarative_switch() -> bool:
    return _DECLARATIVE_SWITCH


@contextmanager
def set_global_declarative_switch() -> Iterator[None]:
    global _DECLARATIVE_SWITCH
    previous = _DECLARATIVE_SWITCH
    _DECLARATIVE_SWITCH = True
    try:
        yield
    finally:
        _DECLARATIVE_SWITCH = previous
