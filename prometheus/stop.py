from pydantic import BaseModel
from prometheus.coord import Coord


class Stop(BaseModel):
    name: str
    coord: Coord
