from pydantic import BaseModel, Field
from prometheus.coord import Coord
from prometheus.car.car_output import CarSearchOutput


class PtransSearchInput(BaseModel):
    start: Coord
    goal: Coord
    start_time: str = Field(alias="start-time")
    car_output: CarSearchOutput = Field(alias="car-output")
