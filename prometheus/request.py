from pydantic import BaseModel
from bus_stop import Stop


class CarRequest(BaseModel):
    stops: list[Stop]
