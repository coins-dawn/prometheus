from pydantic import BaseModel, Field
from datetime import time
from stop import Stop


class SearchInput(BaseModel):
    start_time: time = Field(alias="start-time")
    route_name: str = Field(alias="route-name")
    stops: list[Stop]
