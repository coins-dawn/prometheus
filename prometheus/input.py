from pydantic import BaseModel, Field
from prometheus.stop import Stop


class SearchInput(BaseModel):
    route_name: str = Field(alias="route-name")
    stops: list[Stop]
    start_time: str = Field(alias="start-time")
