from pydantic import BaseModel
from coord import Coord


class Stop(BaseModel):
    coord: Coord
    name: str
