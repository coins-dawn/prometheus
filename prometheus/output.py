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


def get_sample_output():
    return SearchOutout(
        route=OutputRoute(
            distance=100,
            duration=80,
            stops=[
                OutputStop(
                    stop=Stop(coord=Coord(lat=100, lon=200), name="a"), stay_time=10
                ),
                OutputStop(
                    stop=Stop(coord=Coord(lat=200, lon=300), name="b"), stay_time=20
                ),
            ],
            sections=[
                OutputSection(
                    distance=100,
                    duration=100,
                    shape="AAAAAAAAAAAAAAAAAAAAAa",
                )
            ],
        )
    )
