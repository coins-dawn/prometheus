from pydantic import BaseModel
from bus_stop import Stop
from coord import Coord
from datetime import datetime


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
    
class PtransSubroute(BaseModel):
    pass


class PtransResponse(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: datetime
    duration: float
    distance: float
    subroutes: list[PtransSubroute]
