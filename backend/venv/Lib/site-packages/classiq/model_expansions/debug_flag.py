from contextvars import ContextVar

debug_mode: ContextVar[bool] = ContextVar("debug_mode", default=False)
