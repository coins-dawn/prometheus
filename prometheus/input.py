from pydantic import BaseModel, Field
from prometheus.stop import Stop
from prometheus.coord import Coord
from prometheus.output import CarOutputRoute, CarSearchOutout


class CarSearchInput(BaseModel):
    route_name: str = Field(alias="route-name")
    stops: list[Stop]
    start_time: str = Field(alias="start-time")


class PtransSearchInput(BaseModel):
    start: Coord
    goal: Coord
    car_output: CarSearchOutout = Field(alias="car-output")
