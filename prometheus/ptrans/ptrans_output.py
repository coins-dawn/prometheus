from prometheus.coord import Coord
from enum import Enum
from dataclasses import dataclass


class PtransOutputSpotType(str, Enum):
    BUS = "bus"
    WALK = "walk"
    COMBUS = "combus"


class PtransOutputSectionType(str, Enum):
    BUS = "bus"
    WALK = "walk"
    COMBUS = "combus"


@dataclass
class PtransOutputSpot:
    name: str
    coord: Coord
    type: PtransOutputSpotType
    stay_time: int


@dataclass
class PtransOutputSection:
    distance: float
    duration: int
    shape: str
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
