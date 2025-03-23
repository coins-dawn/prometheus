from pydantic import BaseModel

from coord import Coord


class Stop(BaseModel):
    name: str
    coord: Coord
