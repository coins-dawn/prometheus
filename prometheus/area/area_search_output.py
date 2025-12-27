from dataclasses import dataclass
from prometheus.coord import Coord
from prometheus.area.spot_type import SpotType
from shapely.geometry import MultiPolygon


@dataclass
class CombusStop:
    """
    コミュニティバスのバス停を表すクラス。
    """

    id: str = ""
    name: str = ""
    coord: Coord = None

    def to_json(self):
        return {"id": self.id, "name": self.name, "coord": self.coord.to_json()}


@dataclass
class CombusSection:
    """
    コミュニティバスのセクション（バス停からバス停まで）を表すクラス。
    """

    duration_m: int = 0
    distance_km: float = 0.0
    geometry: str = ""

    def to_json(self):
        return {
            "duration-m": self.duration_m,
            "distance-km": self.distance_km,
            "geometry": self.geometry,
        }


@dataclass
class CombusRoute:
    """
    コミュニティバスの経路を表すクラス。
    """

    stop_list: list[CombusStop]
    section_list: list[CombusSection]

    def to_json(self):
        return {
            "stop-list": [stop.to_json() for stop in self.stop_list],
            "section-list": [section.to_json() for section in self.section_list],
        }


@dataclass
class Spot:
    coord: Coord
    spot_type: SpotType
    name: str

    def to_json(self) -> dict:
        return {
            "coord": self.coord.to_json(),
            "spot-type": self.spot_type.value,
            "name": self.name,
        }


@dataclass
class ReachableArea:
    original: MultiPolygon
    with_combus: MultiPolygon
    original_score: int = 0
    with_combus_score: int = 0
    original_score_rate: int = 0
    with_combus_score_rate: int = 0

    def to_json(self) -> dict:
        return {
            "original": self.original.__geo_interface__,
            "with-combus": self.with_combus.__geo_interface__,
            "original-score": self.original_score,
            "with-combus-score": self.with_combus_score,
            "original-score-rate": self.original_score_rate,
            "with-combus-score-rate": self.with_combus_score_rate,
        }


@dataclass
class RoutePoint:
    name: str
    coord: Coord

    def to_json(self) -> dict:
        return {"name": self.name, "coord": self.coord.to_json()}


@dataclass
class RouteSection:
    mode: str
    from_point: RoutePoint
    to_point: RoutePoint
    duration_m: int
    distance_m: int
    geometry: str

    def to_json(self) -> dict:
        return {
            "mode": self.mode,
            "from": self.from_point.to_json(),
            "to": self.to_point.to_json(),
            "duration-m": self.duration_m,
            "distance-m": self.distance_m,
            "geometry": self.geometry,
        }


@dataclass
class Route:
    from_point: RoutePoint
    to_point: RoutePoint
    duration_m: int
    walk_distance_m: int
    distance_m: int
    geometry: str
    sections: list[RouteSection]

    def to_json(self) -> dict:
        return {
            "from": self.from_point.to_json(),
            "to": self.to_point.to_json(),
            "duration-m": self.duration_m,
            "walk-distance-m": self.walk_distance_m,
            "geometry": self.geometry,
            "sections": [section.to_json() for section in self.sections],
            "distance-m": self.distance_m,
        }


@dataclass
class RoutePair:
    original: Route
    with_combus: Route

    def to_json(self) -> dict:
        return {
            "original": self.original.to_json(),
            "with-combus": self.with_combus.to_json(),
        }


@dataclass
class AreaSearchResult:
    spots: list[Spot]
    reachable: ReachableArea
    route_pairs: list[RoutePair]

    def to_json(self) -> dict:
        return {
            "spots": [spot.to_json() for spot in self.spots],
            "reachable": self.reachable.to_json() if self.reachable else None,
            "route-pairs": [route.to_json() for route in self.route_pairs],
        }


@dataclass
class AreaSearchOutput:
    area_search_result: AreaSearchResult
    combus_route: CombusRoute

    def to_json(self) -> dict:
        return {
            "area": self.area_search_result.to_json(),
            "combus": self.combus_route.to_json(),
        }


@dataclass
class AllAreaSearchResult:
    spot: dict
    time_limit: int
    walk_distance_limit: int
    polygon: MultiPolygon
    score: int

    def to_json(self) -> dict:
        return {
            "spot": self.spot,
            "time-limit": self.time_limit,
            "walk-distance-limit": self.walk_distance_limit,
            "polygon": self.polygon.__geo_interface__,
            "score": self.score,
        }


@dataclass
class AllAreaSearchOutput:
    result_list: list[AllAreaSearchResult]

    def to_json(self) -> dict:
        return {"reachables": [result.to_json() for result in self.result_list]}
