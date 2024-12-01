from pydantic import BaseModel
from spot import Spot


class CarSubRoute(BaseModel):
    org: Spot
    dst: Spot
    duration: float
    distance: float
    polyline: str


class CarResponse(BaseModel):
    duration: float
    distance: float
    subroutes: list[CarSubRoute]
