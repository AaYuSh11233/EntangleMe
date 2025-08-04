from typing import NewType

from classiq.interface.analyzer.result import DataID
from classiq.interface.exceptions import ClassiqAPIError

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper

SerializedVisualModel = NewType("SerializedVisualModel", str)


async def visualize_async(
    data_id: DataID,
) -> SerializedVisualModel:
    try:
        visual_model = await ApiWrapper.call_get_visual_model(data_id.id)
    except ClassiqAPIError as error:
        if error.status_code != 404:
            raise error
        analyzer_data = await ApiWrapper.get_analyzer_app_data(data_id)
        visual_model = await ApiWrapper.call_visualization_task(analyzer_data)
    return SerializedVisualModel(visual_model.model_dump_json(indent=2))


def visualize(
    data_id: DataID,
) -> SerializedVisualModel:
    result = async_utils.run(visualize_async(data_id))
    return result


__all__ = [
    "SerializedVisualModel",
    "visualize",
]
