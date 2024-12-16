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


class BusInfo(BaseModel):
    """バス経路の情報を表すクラス。"""

    agency: str
    line_name: str
    org_stop_name: str
    dst_stop_name: str


class PtransSubroute(BaseModel):
    """徒歩＋公共交通の個別経路を表すクラス。"""

    mode: str
    start_time: str
    goal_time: str
    distance: float
    duration: float
    polyline: str
    bus_info: BusInfo | None


class PtransResponse(BaseModel):
    """徒歩＋公共交通の経路情報を表すクラス。"""

    org_coord: Coord
    dst_coord: Coord
    start_time: str
    goal_time: str
    duration: float
    subroutes: list[PtransSubroute]


class CombinedResponse(PtransResponse):
    """徒歩＋公共交通＋コミュニティバスの経路情報を表すクラス。"""
    pass
