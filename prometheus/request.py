from pydantic import BaseModel, Field
from bus_stop import Stop
from coord import Coord
from datetime import time


class CarRequest(BaseModel):
    stops: list[Stop]
    start_time_list: list[time]
    debug: bool


class PtransRequest(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


class CombinedRequest(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: str
    use_route_id: str
