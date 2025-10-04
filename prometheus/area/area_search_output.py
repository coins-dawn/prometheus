from dataclasses import dataclass
from prometheus.coord import Coord
from prometheus.area.spot_type import SpotType
from shapely.geometry.polygon import Polygon


@dataclass
class Spot:
    coord: Coord
    spot_type: SpotType
    name: str

    def to_json(self) -> dict:
        return {
            "coord": self.coord.to_json(),
            "spot_type": self.spot_type.value,
            "name": self.name,
        }


@dataclass
class ReachableArea:
    original: Polygon
    with_comnuter: Polygon

    def to_json(self) -> dict:
        return {
            "original": self.original.__geo_interface__,
            "with_combus": (
                self.with_comnuter.__geo_interface__ if self.with_comnuter else None
            ),
        }


@dataclass
class AreaSearchResult:
    spots: list[Spot]
    reachable: ReachableArea

    def to_json(self) -> dict:
        return {
            "spots": [spot.to_json() for spot in self.spots],
            "reachable": self.reachable.to_json() if self.reachable else None,
        }


@dataclass
class AreaSearchOutput:
    result_dict: dict[SpotType, AreaSearchResult]

    def to_json(self) -> dict:
        return {
            spot_type.value: result.to_json()
            for spot_type, result in self.result_dict.items()
        }
