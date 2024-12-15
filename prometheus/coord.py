from pydantic import BaseModel


class Coord(BaseModel):
    lat: float
    lon: float

    class Config:
        frozen = True
