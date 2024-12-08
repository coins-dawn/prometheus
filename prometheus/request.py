from pydantic import BaseModel
from bus_stop import Stop
from coord import Coord
from datetime import datetime, time


class CarRequest(BaseModel):
    stops: list[Stop]
    start_time_list: list[time]
    debug: bool


class PtransRequest(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: datetime
