from pydantic import BaseModel
from bus_stop import Stop
from coord import Coord
from datetime import datetime, time


class CarSubRoute(BaseModel):
    """バス停からバス停の一つの区間を表すクラス。"""

    org: Stop
    dst: Stop
    duration: float
    distance: float
    polyline: str


class RouteInfo(BaseModel):
    """コミュニティバスの経路を表すクラス。"""

    duration: float
    distance: float
    subroutes: list[CarSubRoute]


class TimeTableElement(BaseModel):
    """ひとつのバス停の時刻表を表すクラス。"""

    stop_name: str
    time_list: list[str]


class CarResponse(BaseModel):
    """車経路探索の結果を表すクラス。"""

    route_id: str
    route_info: RouteInfo
    time_table: list[TimeTableElement]


class PtransSubroute(BaseModel):
    pass


class PtransResponse(BaseModel):
    org_coord: Coord
    dst_coord: Coord
    start_time: datetime
    duration: float
    distance: float
    subroutes: list[PtransSubroute]
