from classiq.interface.helpers.versioned_model import VersionedModel


class AnglesResult(VersionedModel):
    initial_point: list[float]


class PyomoObjectResult(VersionedModel):
    details: str
