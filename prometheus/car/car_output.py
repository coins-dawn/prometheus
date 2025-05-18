from dataclasses import dataclass
from prometheus.stop import Stop


@dataclass
class CarOutputStop:
    stop: Stop
    stay_time: int
    departure_times: list[str]


@dataclass
class CarOutputSection:
    distance: float
    duration: int
    shape: str


@dataclass
class CarOutputRoute:
    distance: float
    duration: int
    stops: list[CarOutputStop]
    sections: list[CarOutputSection]


@dataclass
class CarSearchOutput:
    route: CarOutputRoute
