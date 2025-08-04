import asyncio
from collections.abc import Awaitable
from functools import wraps
from typing import TYPE_CHECKING, Callable

from ipywidgets import widgets  # type: ignore[import]

if TYPE_CHECKING:
    from classiq._analyzer_extras.interactive_hardware import InteractiveHardware

WidgetName = str
WidgetValue = str
WidgetFunc = Callable[["InteractiveHardware", WidgetValue], Awaitable[None]]

SleepTime = 0.01

# for understanding butter the meaning of these decorators/functions look at:
# https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Asynchronous.html?highlight=unobserve

# The small slipping times  are for being able to trigger the graph with a code
# and not only by the press on the widget. For reasons that are not totally clear
# when python command is send those tiny await slipping times are need in order
# for the graph to respond.

# ToDo - benchmark the sleeping that are needed for the interactive graph:
#  https://classiq.atlassian.net/browse/CAD-2821


def widget_callback(widget_name: WidgetName) -> Callable[[WidgetFunc], Callable]:
    def decorator(function: WidgetFunc) -> Callable:
        @wraps(function)
        async def wrapper(self: "InteractiveHardware", **kwargs: WidgetValue) -> None:
            widget: widgets = getattr(self, widget_name)
            interactive_loop = _create_interactive_loop_async(
                function=function, self=self, widget=widget
            )
            asyncio.ensure_future(interactive_loop)  # noqa: RUF006
            await asyncio.sleep(SleepTime)

        return wrapper

    return decorator


async def _create_interactive_loop_async(
    function: WidgetFunc, self: "InteractiveHardware", widget: widgets
) -> None:
    while True:
        value: WidgetValue = await _wait_for_change(widget=widget)
        await asyncio.sleep(SleepTime)
        await function(self, value)


def _wait_for_change(widget: widgets) -> asyncio.Future:
    future: asyncio.Future = asyncio.Future()

    def _get_value(change) -> None:  # type: ignore[no-untyped-def]
        future.set_result(change.new)
        widget.unobserve(_get_value, "value")

    widget.observe(_get_value, "value")
    return future
