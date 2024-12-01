from pydantic import BaseModel
from coord import Coord


class Spot(BaseModel):
    coord: Coord
    name: str
