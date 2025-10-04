from pydantic import BaseModel


class Coord(BaseModel):
    lat: float
    lon: float

    def to_json(self) -> dict:
        return {"lat": self.lat, "lon": self.lon}
