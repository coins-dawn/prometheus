from pydantic import BaseModel


class Coord(BaseModel):
    lat: float
    lon: float
