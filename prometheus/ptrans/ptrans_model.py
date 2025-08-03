from dataclasses import dataclass
from enum import Enum

from prometheus.coord import Coord


class TransitType(Enum):
    """交通手段の種類を表す列挙型"""

    WALK = "walk"  # 徒歩
    BUS = "bus"  # バス
    COMBUS = "combus"  # コミュニティバス


@dataclass
class Node:
    """ネットワーク中のノードを表すクラス。"""

    node_id: str
    name: str
    coord: Coord


@dataclass
class Edge:
    """ノード間のエッジを表すデータクラス"""

    org_node_id: str
    dst_node_id: str
    travel_time: int  # 移動時間[分]
    transit_type: TransitType  # 交通手段の種類


@dataclass
class TimeTable:
    """時刻表を表すクラス。"""

    weekday: list[str]  # 平日の時刻表
    holiday: list[str]  # 休日の時刻表
    # TODO 名称は時刻表に入っているべきではないので分離する
    weekday_name: str  # 平日の路線名称
    holiday_name: str  # 休日の路線名称


@dataclass
class CombusEdge:
    org_node_id: str
    dst_node_id: str
    duration: int
    name: str
    shape: str
    time_tables: TimeTable


@dataclass
class EntryResult:
    node: Node
    distance: int


@dataclass
class SearchResult:
    sections: list[Edge]


@dataclass
class AdjacentDictElem:
    node: Node
    cost: int
    transit_type: TransitType
