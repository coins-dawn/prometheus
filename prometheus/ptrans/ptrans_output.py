from prometheus.coord import Coord
from enum import Enum
from dataclasses import dataclass


class PtransOutputSectionType(str, Enum):
    BUS = "bus"
    WALK = "walk"
    COMBUS = "combus"


@dataclass
class PtransOutputSpot:
    name: str
    coord: Coord


@dataclass
class PtransOutputSection:
    duration: int
    shape: str  # polyline or ""
    start_time: str
    goal_time: str
    type: PtransOutputSectionType
    name: str


@dataclass
class PtransOutputRoute:
    start_time: str
    goal_time: str
    duration: int
    spots: list[PtransOutputSpot]
    sections: list[PtransOutputSection]


@dataclass
class PtransSearchOutput:
    route: PtransOutputRoute
