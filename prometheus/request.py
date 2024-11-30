from pydantic import BaseModel
from typing import Optional
from coord import Coord


class CarRequest(BaseModel):
    org: Coord
    dst: Coord
    vias: list[Coord]
