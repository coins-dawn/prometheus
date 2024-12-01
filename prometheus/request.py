from pydantic import BaseModel
from spot import Spot


class CarRequest(BaseModel):
    org: Spot
    dst: Spot
    vias: list[Spot]
