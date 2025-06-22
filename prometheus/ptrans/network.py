import pandas
import random
import json
import math
import heapq
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from prometheus.coord import Coord
from prometheus.car.car_output import CarOutputRoute

STOP_FILE_PATH = "data/gtfs/stops.txt"
TRAVEL_TIME_FILE_PATH = "data/gtfs/average_travel_times.csv"
SHAPE_FILE_PATH = "data/gtfs/shapes.json"
TRIP_PAIRS_FILE_PATH = "data/gtfs/trip_pairs.json"

WALK_SPEED = 50  # メートル/分。直線距離ベースなので少し遅めにしている


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
    lat: float
    lon: float


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

    weekday: List[str]  # 平日の時刻表
    holiday: List[str]  # 休日の時刻表
    # TODO 名称は時刻表に入っているべきではないので分離する
    weekday_name: str  # 平日の路線名称
    holiday_name: str  # 休日の路線名称


@dataclass
class CombusNode:
    id: str
    name: str
    lat: float
    lon: float


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
    sections: List[Edge]


def haversine(lat1, lon1, lat2, lon2) -> int:
    """2点間の概算距離を求める（ハーバーサイン距離）"""
    R = 6371  # 地球半径 (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return int(R * c * 1000)  # m に変換


def convert_car_route_2_combus_data(
    car_output: CarOutputRoute,
) -> Tuple[List[CombusEdge], List[CombusNode]]:
    # 新しいノードIDを採番
    random.seed(0)
    nodeid_list = []
    for _ in car_output.stops:
        new_nodeid = f"A{random.randint(1000, 9999)}"
        nodeid_list.append(new_nodeid)

    # エッジの追加
    combus_edges = []
    for i, section in enumerate(car_output.sections):
        org_nodeid = nodeid_list[i]
        dst_nodeid = nodeid_list[i + 1] if i + 1 < len(nodeid_list) else nodeid_list[0]
        # TODO 時刻表はsectionに入れるべき？
        time_table = TimeTable(
            weekday=car_output.stops[i].departure_times,
            holiday=car_output.stops[i].departure_times,
            weekday_name="コミュニティバス",
            holiday_name="コミュニティバス",
        )
        combus_edges.append(
            CombusEdge(
                org_node_id=org_nodeid,
                dst_node_id=dst_nodeid,
                duration=section.duration,
                name="コミュニティバス",
                shape=section.shape,
                time_tables=time_table,
            )
        )

    # ノードの追加
    combus_nodes = []
    for i, stop in enumerate(car_output.stops):
        combus_nodes.append(
            CombusNode(
                id=nodeid_list[i],
                name=f"バス停{i+1}",
                lat=stop.stop.coord.lat,
                lon=stop.stop.coord.lon,
            )
        )

    return combus_edges, combus_nodes


def trace_path(prev_nodes: Dict[int, int], goal_node: int) -> List[int]:
    """ゴールノードからスタートノードまでの経路をトレース"""
    node_id_list = []
    node = goal_node
    while node in prev_nodes:
        node_id_list.append(node)
        node = prev_nodes[node]
    node_id_list.append(node)  # スタートノードを追加
    return node_id_list[::-1]  # 経路を逆順にして返す


class Tracer:
    """経路確定後に時刻表を参照してトレースを行うクラス。"""

    def __init__(self) -> None:
        self.shape_dict: Dict[Tuple[str, str], str] = self._load_shape_dict(
            SHAPE_FILE_PATH
        )
        self.time_table_dict: Dict[Tuple[str, str], TimeTable] = (
            self._load_time_table_dict()
        )

    def _load_shape_dict(self, shape_file_path: str) -> dict[tuple[str, str], str]:
        """shapes.jsonを読み込んで (from, to) -> polyline文字列 のdictを返す"""
        shape_dict: dict[tuple[str, str], str] = {}
        with open(shape_file_path, "r", encoding="utf-8") as f:
            shapes = json.load(f)
            for entry in shapes:
                org = entry["stop_from"]
                dst = entry["stop_to"]
                polyline_str = entry["shape"]
                shape_dict[(org, dst)] = polyline_str
        return shape_dict

    def _load_time_table_dict() -> dict[tuple[str, str], TimeTable]:
        """trip_pairs.jsonを読み込んで (from, to) -> 時刻表 のdictを返す"""
        time_table_dict: dict[tuple[str, str], TimeTable] = {}
        with open(TRIP_PAIRS_FILE_PATH, "r", encoding="utf-8") as f:
            trip_pairs = json.load(f)
            for entry in trip_pairs:
                org = entry["stop_from"]
                dst = entry["stop_to"]
                time_table_dict[(org, dst)] = TimeTable(
                    weekday=entry["departure_times"],
                    holiday=entry["departure_times"],
                    weekday_name="コミュニティバス",
                    holiday_name="コミュニティバス",
                )
        return time_table_dict

    def add_combus_to_trace_data(self, combus: CarOutputRoute) -> None:
        pass


class Searcher:
    """経路探索を行い最適経路を求めるクラス。"""

    def __init__(self) -> None:
        self.node_dict: Dict[str, Node] = self._load_node_dict(STOP_FILE_PATH)
        self.edge_dict: Dict[Tuple[str, str], Edge] = self._load_edge_dict(
            TRAVEL_TIME_FILE_PATH
        )
        self.adjacent_edge_dict: Dict[str, List[Tuple[Edge, int, TransitType]]] = (
            self._create_adjacent_edges_dict()
        )

    def _load_node_dict(self, stops_file: str) -> Dict[str, Node]:
        stops_df = pandas.read_csv(stops_file)
        node_dict: Dict[str, Node] = {}
        for _, row in stops_df.iterrows():
            node_dict[row["stop_id"]] = Node(
                node_id=row["stop_id"],
                name=row["stop_name"],
                lat=float(row["stop_lat"]),
                lon=float(row["stop_lon"]),
            )
        return node_dict

    def _load_edge_dict(
        self, travel_time_file_path: str
    ) -> Dict[Tuple[str, str], Edge]:
        travel_df = pandas.read_csv(travel_time_file_path)
        edge_dict: Dict[Tuple[str, str], Edge] = {}
        for _, row in travel_df.iterrows():
            edge_dict[(row["stop_from"], row["stop_to"])] = Edge(
                org_node_id=row["stop_from"],
                dst_node_id=row["stop_to"],
                travel_time=float(row["average_travel_time"]),
                transit_type=TransitType.BUS,
            )
        return edge_dict

    def _create_adjacent_edges_dict(
        self,
    ) -> Dict[str, List[Tuple[Edge, int, TransitType]]]:
        adjacent_edge_dict: Dict[str, List[Tuple[Edge, int, TransitType]]] = {}
        for (org, dst), edge in self.edge_dict.items():
            if org not in adjacent_edge_dict:
                adjacent_edge_dict[org] = []
            adjacent_edge_dict[org].append((edge, dst, edge.transit_type))
        return adjacent_edge_dict

    def add_combus_to_search_network(
        self, combus_nodes: List[CombusNode], combus_edges: List[CombusEdge]
    ) -> None:
        for node in combus_nodes:
            self.node_dict[node.id] = Node(
                node_id=node.id,
                name=node.name,
                lat=node.lat,
                lon=node.lon,
            )
        for edge in combus_edges:
            self.edge_dict[(edge.org_node_id, edge.dst_node_id)] = Edge(
                org_node_id=edge.org_node_id,
                dst_node_id=edge.dst_node_id,
                travel_time=edge.duration,
                transit_type=TransitType.COMBUS,
            )

        # 既存のバス停から徒歩10分いないなら徒歩エッジを追加
        for combus_node in combus_nodes:
            for node_id, node in self.node_dict.items():
                distance_to_add_node = haversine(
                    node.lat, node.lon, combus_node.lat, combus_node.lon
                )
                walk_time = distance_to_add_node / WALK_SPEED
                if walk_time < 10:
                    self.edge_dict[(node_id, combus_node.id)] = Edge(
                        org_node_id=node_id,
                        dst_node_id=combus_node.id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )
                    self.edge_dict[(combus_node.id, node_id)] = Edge(
                        org_node_id=combus_node.id,
                        dst_node_id=node_id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )

    def find_nearest_node(self, target_coord: Coord, k: int = 10) -> List[EntryResult]:
        """指定した地点に最も近いノードをk件返す"""
        distances = {
            stop_id: haversine(target_coord.lat, target_coord.lon, coord.lat, coord.lon)
            for stop_id, coord in self.node_dict.items()
        }
        nearest_nodes = sorted(distances, key=distances.get)[:k]
        return [
            EntryResult(node=self.node_dict[nid], distance=distances[nid])
            for nid in nearest_nodes
        ]

    def search(
        self, start_candidates: List[EntryResult], goal_candidates: List[EntryResult]
    ) -> List[Edge]:
        def calc_additional_cost(prev_mode: TransitType, next_mode: TransitType) -> int:
            if prev_mode == TransitType.BUS and next_mode == TransitType.BUS:
                return 10
            if prev_mode == TransitType.WALK and next_mode == TransitType.BUS:
                return 10
            return 0

        pq: List[Tuple[float, Node, TransitType]] = []  # ポテンシャル、ノード、交通手段
        costs: Dict[int, float] = {}
        prev_nodes: Dict[int, int] = {}  # start空の拡散結果における、ひとつ前のノードID

        for start in start_candidates:
            heapq.heappush(
                pq, (start.distance / WALK_SPEED, start.node, TransitType.WALK)
            )
            costs[start.node.node_id] = start.distance / WALK_SPEED

        while pq:
            curr_cost, node, prev_mode = heapq.heappop(pq)

            if node in goal_candidates:
                # 経路をトレースしてエッジ列に変換
                node_id_list = trace_path(prev_nodes, node)
                edge_list = []
                for i in range(len(node_id_list) - 1):
                    org_node_id = node_id_list[i]
                    dst_node_id = node_id_list[i + 1]
                    edge = self.edge_dict.get((org_node_id, dst_node_id))
                    edge_list.append(edge)
                return SearchResult(sections=edge_list)

            for neighbor, weight, mode in self.adjacent_edge_dict.get(node.node_id, []):
                new_cost = curr_cost + weight + calc_additional_cost(prev_mode, mode)
                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    prev_nodes[neighbor] = node
                    heapq.heappush(pq, (new_cost, neighbor, mode))
        return None
