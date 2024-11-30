from pydantic import BaseModel
from typing import Optional
from coord import Coord


class Request(BaseModel):
    org: Coord
    dst: Coord
    vias: list[Coord]
