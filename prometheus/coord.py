from dataclasses import dataclass


@dataclass
class Coord:
    lat: float
    lon: float

    def to_json(self) -> dict:
        return {"lat": self.lat, "lon": self.lon}
