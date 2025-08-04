from typing import Any, Optional

import pydantic

from classiq.interface.enum_utils import StrEnum
from classiq.interface.helpers.versioned_model import VersionedModel


class CytoScapePosition(pydantic.BaseModel):
    x: int = pydantic.Field(
        default=..., description="X coordinate in the Cytoscape View"
    )
    y: int = pydantic.Field(
        default=..., description="Y coordinate in the Cytoscape View"
    )


class CytoScapeEdgeData(pydantic.BaseModel):
    source: str = pydantic.Field(
        default=" ", description="the Id of the Node that is the Source of the edge"
    )
    target: str = pydantic.Field(
        default=" ", description="the Id of the Node that is the Target the edge"
    )

    @pydantic.model_validator(mode="before")
    @classmethod
    def _validate_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["source"] = str(values["source"]) or " "
        values["target"] = str(values["target"]) or " "
        return values


class CytoScapeEdge(pydantic.BaseModel):
    data: CytoScapeEdgeData = pydantic.Field(
        description="Edge's Data, mainly the source and target of the Edge"
    )


class CytoScapeNode(pydantic.BaseModel):
    data: dict[str, Any] = pydantic.Field(
        default=...,
        description="Data of the Node, such as label, and color, can be of free form",
    )
    position: Optional[CytoScapePosition] = pydantic.Field(
        default=..., description="Position of the Node to be rendered in Cytocape"
    )


class CytoScapeGraph(pydantic.BaseModel):
    nodes: list[CytoScapeNode] = pydantic.Field(
        default_factory=list,
        description="Nodes of the Graph",
    )
    edges: list[CytoScapeEdge] = pydantic.Field(
        default_factory=list,
        description="Edges of the Graph",
    )


class ConnectivityErrors(StrEnum):
    EMPTY = ""
    DEVICE_NOT_AVAILABLE_ERROR_MSG = (
        "HW connectivity map temporarily unavailable for this Device"
    )


class HardwareConnectivityGraphResult(VersionedModel):
    graph: Optional[CytoScapeGraph] = pydantic.Field(
        default=...,
        description="The Cytoscape graph in the desired Structure for the FE",
    )
    error: ConnectivityErrors = pydantic.Field(
        default=ConnectivityErrors.EMPTY,
        description="Any errors encountered while generating the graph",
    )
