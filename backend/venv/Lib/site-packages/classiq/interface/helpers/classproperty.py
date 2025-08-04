from typing import TYPE_CHECKING, Any, Optional


class classproperty(property):  # noqa: N801
    def __get__(self, owner_self: Any, owner_cls: Optional[type] = None) -> Any:
        if TYPE_CHECKING:
            assert self.fget is not None
        return self.fget(owner_cls)
