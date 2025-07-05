import pandas
import random
import json
import math
import heapq
import itertools
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from utility import add_time
from prometheus.coord import Coord
from prometheus.car.car_output import CarOutputRoute
from prometheus.ptrans.ptrans_output import (
    PtransOutputSection,
    PtransSearchOutput,
    PtransOutputRoute,
    PtransOutputSpot,
    PtransOutputSectionType,
)


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

    weekday: List[str]  # 平日の時刻表
    holiday: List[str]  # 休日の時刻表
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
    sections: List[Edge]


def haversine(coord1: Coord, coord2: Coord) -> int:
    """2点間の概算距離を求める（ハーバーサイン距離）"""
    R = 6371  # 地球半径 (km)
    dlat = math.radians(coord2.lat - coord1.lat)
    dlon = math.radians(coord2.lon - coord1.lon)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(coord1.lat))
        * math.cos(math.radians(coord2.lat))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return int(R * c * 1000)  # m に変換


def convert_car_route_2_combus_data(
    car_output: CarOutputRoute,
) -> Tuple[List[CombusEdge], List[Node]]:
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
            Node(node_id=nodeid_list[i], name=f"バス停{i+1}", coord=stop.stop.coord)
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


def find_next_bus_time(current_time: str, time_table: List[str]):
    """
    現在時刻と時刻表から次のバスの時刻を探す。
    終電が終わってしまった場合にはNoneを返す。
    """
    h, m = map(int, current_time.split(":"))
    current_minutes = h * 60 + m
    for bus_time in time_table:
        bh, bm = map(int, bus_time.split(":"))
        bus_minutes = bh * 60 + bm
        if bus_minutes > current_minutes:
            return bus_time[:5]
    return None


class Tracer:
    """経路確定後に時刻表を参照してトレースを行うクラス。"""

    def __init__(self, node_dict: Dict[str, Node]) -> None:
        self.shape_dict: Dict[Tuple[str, str], str] = self._load_shape_dict(
            SHAPE_FILE_PATH
        )
        self.time_table_dict: Dict[Tuple[str, str], TimeTable] = (
            self._load_time_table_dict()
        )
        self.node_dict: Dict[str, Node] = node_dict

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

    def _load_time_table_dict(self) -> dict[tuple[str, str], TimeTable]:
        """trip_pairs.jsonを読み込んで (from, to) -> 時刻表 のdictを返す"""
        time_table_dict: dict[tuple[str, str], TimeTable] = {}
        with open(TRIP_PAIRS_FILE_PATH, "r", encoding="utf-8") as f:
            trip_pairs = json.load(f)
            for entry in trip_pairs:
                org = entry["stop_from"]
                dst = entry["stop_to"]
                time_table_dict[(org, dst)] = TimeTable(
                    weekday=entry["trip"]["weekday"]["time_table"],
                    holiday=entry["trip"]["holiday"]["time_table"],
                    weekday_name=entry["trip"]["weekday"]["name"],
                    holiday_name=entry["trip"]["holiday"]["name"],
                )
        return time_table_dict

    def add_combus_to_trace_data(self, combus_edges: List[CombusEdge]) -> None:
        for combus_edge in combus_edges:
            self.shape_dict[(combus_edge.org_node_id, combus_edge.dst_node_id)] = (
                combus_edge.shape
            )
            self.time_table_dict[(combus_edge.org_node_id, combus_edge.dst_node_id)] = (
                combus_edge.time_tables
            )

    def create_output_section(self, edge, current_time: str) -> PtransOutputSection:
        is_edge = isinstance(edge, Edge)

        # 徒歩セクションの場合
        if is_edge and edge.transit_type == TransitType.WALK:
            return PtransOutputSection(
                duration=edge.travel_time,
                shape="",
                start_time=current_time,
                goal_time=add_time(current_time, edge.travel_time),
                name="徒歩",
                type=PtransOutputSectionType.WALK,
            )

        # 通常バスのセクションの場合
        if is_edge:
            shape = self.shape_dict.get((edge.org_node_id, edge.dst_node_id), "")
            time_table = self.time_table_dict.get(
                (edge.org_node_id, edge.dst_node_id), None
            )
            bus_time_list = time_table.weekday  # 平日で決め打ち
            start_time = find_next_bus_time(current_time, bus_time_list)
            return PtransOutputSection(
                duration=edge.travel_time,
                shape=shape,
                start_time=start_time,
                goal_time=add_time(start_time, edge.travel_time),
                name=time_table.weekday_name,  # 平日で決め打ち
                type=PtransOutputSectionType.BUS,
            )

        # コミュニティバスの場合
        shape = edge.shape
        time_table = edge.time_tables
        bus_time_list = time_table.weekday  # 平日で決め打ち
        start_time = find_next_bus_time(current_time, bus_time_list)
        return PtransOutputSection(
            duration=edge.duration,
            shape=shape,
            start_time=start_time,
            goal_time=add_time(start_time, edge.duration),
            name=time_table.weekday_name,  # 平日で決め打ち
            type=PtransOutputSectionType.COMBUS,
        )

    def create_sections(
        self,
        search_result: SearchResult,
        start_time: str,
        start_coord: Coord,
        goal_coord: Coord,
    ) -> List[PtransOutputSection]:
        output_section_list: List[PtransOutputSection] = []

        # 出発地～最初のバス停
        first_bus_id = search_result.sections[0].org_node_id
        first_bus_node = self.node_dict[first_bus_id]
        first_bus_coord = first_bus_node.coord
        start_to_first_bus_stop_distance = haversine(start_coord, first_bus_coord)
        start_to_first_bus_stop_time = int(
            start_to_first_bus_stop_distance / WALK_SPEED
        )
        current_time = add_time(start_time, start_to_first_bus_stop_time)
        output_section_list.append(
            PtransOutputSection(
                duration=start_to_first_bus_stop_time,
                shape="",
                start_time=start_time,
                goal_time=current_time,
                name="徒歩",
                type=PtransOutputSectionType.WALK,
            )
        )

        # 最初のバス停～最後のバス停
        for edge in search_result.sections:
            output_section = self.create_output_section(edge, current_time)
            output_section_list.append(output_section)
            current_time = output_section.goal_time

        # 最後のバス停～目的地

        return output_section_list

    def create_spots(self) -> List[PtransOutputSpot]:
        return []

    def trace(
        self,
        search_result: SearchResult,
        start_time: str,
        start_coord: Coord,
        goal_coord: Coord,
    ) -> PtransSearchOutput:
        sections = self.create_sections(
            search_result, start_time, start_coord, goal_coord
        )
        spots = self.create_spots()
        goal_time = start_time  # ゴール時刻は後で設定
        duration = 0  # 後で設定

        return PtransSearchOutput(
            PtransOutputRoute(
                start_time=start_time,
                goal_time=goal_time,
                duration=duration,
                spots=spots,
                sections=sections,
            )
        )


@dataclass
class AdjacentDictElem:
    node: Node
    cost: int
    transit_type: TransitType


class Searcher:
    """経路探索を行い最適経路を求めるクラス。"""

    def __init__(self) -> None:
        self.node_dict: Dict[str, Node] = self._load_node_dict(STOP_FILE_PATH)
        self.edge_dict: Dict[Tuple[str, str], Edge] = self._load_edge_dict(
            TRAVEL_TIME_FILE_PATH
        )
        self.adjacent_dict: Dict[str, List[AdjacentDictElem]] = (
            self._create_adjacent_edges_dict()
        )

    def _load_node_dict(self, stops_file: str) -> Dict[str, Node]:
        stops_df = pandas.read_csv(stops_file)
        node_dict: Dict[str, Node] = {}
        for _, row in stops_df.iterrows():
            node_dict[row["stop_id"]] = Node(
                node_id=row["stop_id"],
                name=row["stop_name"],
                coord=Coord(lat=float(row["stop_lat"]), lon=float(row["stop_lon"])),
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

        # 徒歩のエッジを追加
        for node_id_1, node_id_2 in itertools.combinations(self.node_dict.keys(), 2):
            node1 = self.node_dict[node_id_1]
            node2 = self.node_dict[node_id_2]
            distance = haversine(node1.coord, node2.coord)
            walk_time = distance / WALK_SPEED
            if walk_time < 10:
                edge_dict[(node_id_1, node_id_2)] = Edge(
                    org_node_id=node_id_1,
                    dst_node_id=node_id_2,
                    travel_time=walk_time,
                    transit_type=TransitType.WALK,
                )
                edge_dict[(node_id_2, node_id_1)] = Edge(
                    org_node_id=node_id_2,
                    dst_node_id=node_id_1,
                    travel_time=walk_time,
                    transit_type=TransitType.WALK,
                )
        return edge_dict

    def _create_adjacent_edges_dict(
        self,
    ) -> Dict[str, List[AdjacentDictElem]]:
        adjacent_dict: Dict[str, List[AdjacentDictElem]] = {}
        for (org, dst), edge in self.edge_dict.items():
            if org not in adjacent_dict:
                adjacent_dict[org] = []
            adjacent_dict[org].append(
                AdjacentDictElem(
                    node=self.node_dict[dst],
                    cost=edge.travel_time,
                    transit_type=edge.transit_type,
                )
            )
        return adjacent_dict

    def add_combus_to_search_network(
        self, combus_nodes: List[Node], combus_edges: List[CombusEdge]
    ) -> None:
        for node in combus_nodes:
            self.node_dict[node.node_id] = Node(
                node_id=node.node_id,
                name=node.name,
                coord=node.coord,
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
                # node.coordとcombus_node.coordの型をチェック
                if not isinstance(node, Node) or not isinstance(combus_node, Node):
                    raise TypeError("node and combus_node must be Node instances")
                distance_to_add_node = haversine(node.coord, combus_node.coord)
                walk_time = distance_to_add_node / WALK_SPEED
                if walk_time < 10:
                    self.edge_dict[(node_id, combus_node.node_id)] = Edge(
                        org_node_id=node_id,
                        dst_node_id=combus_node.node_id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )
                    self.edge_dict[(combus_node.node_id, node_id)] = Edge(
                        org_node_id=combus_node.node_id,
                        dst_node_id=node_id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )

    def find_nearest_node(self, target_coord: Coord, k: int = 10) -> List[EntryResult]:
        """指定した地点に最も近いノードをk件返す"""
        distances = {
            stop_id: haversine(target_coord, node.coord)
            for stop_id, node in self.node_dict.items()
        }
        nearest_nodes = sorted(distances, key=distances.get)[:k]
        return [
            EntryResult(node=self.node_dict[nid], distance=distances[nid])
            for nid in nearest_nodes
        ]

    def search(
        self, start_candidates: List[EntryResult], goal_candidates: List[EntryResult]
    ) -> SearchResult:
        def calc_additional_cost(prev_mode: TransitType, next_mode: TransitType) -> int:
            if prev_mode == TransitType.BUS and next_mode == TransitType.BUS:
                return 10
            if prev_mode == TransitType.WALK and next_mode == TransitType.BUS:
                return 10
            return 0

        pq: List[Tuple[float, int, TransitType]] = (
            []
        )  # ポテンシャル、ノードID、交通手段
        costs: Dict[int, float] = {}
        prev_nodes: Dict[int, int] = {}  # start空の拡散結果における、ひとつ前のノードID

        for start in start_candidates:
            heapq.heappush(
                pq, (start.distance / WALK_SPEED, start.node.node_id, TransitType.WALK)
            )
            costs[start.node.node_id] = start.distance / WALK_SPEED

        goal_candidates_nodeid_list = [goal.node.node_id for goal in goal_candidates]

        while pq:
            curr_cost, node_id, prev_mode = heapq.heappop(pq)

            # !bug
            # ゴールノードについては最適なものではなく、
            # 最初に選ばれたものが選ばれている
            if node_id in goal_candidates_nodeid_list:
                # 経路をトレースしてエッジ列に変換
                node_id_list = trace_path(prev_nodes, node_id)
                edge_list = []
                for i in range(len(node_id_list) - 1):
                    org_node_id = node_id_list[i]
                    dst_node_id = node_id_list[i + 1]
                    edge = self.edge_dict.get((org_node_id, dst_node_id))
                    edge_list.append(edge)
                return SearchResult(sections=edge_list)

            for adjacent_elem in self.adjacent_dict.get(node_id, []):
                adjacent_node_id = adjacent_elem.node.node_id
                weight = adjacent_elem.cost
                mode = adjacent_elem.transit_type
                new_cost = curr_cost + weight + calc_additional_cost(prev_mode, mode)
                if adjacent_node_id not in costs or new_cost < costs[adjacent_node_id]:
                    costs[adjacent_node_id] = new_cost
                    prev_nodes[adjacent_node_id] = node_id
                    heapq.heappush(pq, (new_cost, adjacent_node_id, mode))
        return None
