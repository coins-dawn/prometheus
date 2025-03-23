from dataclasses import dataclass

from stop import Stop
from coord import Coord


@dataclass
class OutputStop:
    stop: Stop
    stay_time: int


@dataclass
class OutputSection:
    distance: float
    duration: int
    shape: str


@dataclass
class OutputRoute:
    distance: float
    duration: int
    stops: list[OutputStop]
    sections: list[OutputSection]


@dataclass
class SearchOutout:
    route: OutputRoute
