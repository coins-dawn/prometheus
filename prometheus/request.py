from pydantic import BaseModel
from bus_stop import Stop
from coord import Coord
from datetime import datetime


class CarRequest(BaseModel):
    stops: list[Stop]


class PtransRequest(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: datetime
