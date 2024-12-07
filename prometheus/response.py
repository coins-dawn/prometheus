from pydantic import BaseModel
from bus_stop import Stop


class CarSubRoute(BaseModel):
    org: Stop
    dst: Stop
    duration: float
    distance: float
    polyline: str


class CarResponse(BaseModel):
    route_id: str
    duration: float
    distance: float
    subroutes: list[CarSubRoute]


class PtransResponse(BaseModel):
    pass
