from dataclasses import dataclass
from prometheus.stop import Stop


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
