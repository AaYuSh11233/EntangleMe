from typing import Any, Callable

CUSTOM_ENCODERS: dict[type, Callable[[Any], Any]] = {complex: str}
