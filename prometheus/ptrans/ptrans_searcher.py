import pandas
import random
import json
import math
import heapq
import itertools
import pprint
import polyline
from typing import Dict, List, Tuple

from prometheus.utility import (
    add_time,
    sub_time,
    convert_time_int_2_str,
    convert_time_str_2_int,
)
from prometheus.coord import Coord
from prometheus.car.car_output import CarOutputRoute
from prometheus.ptrans.ptrans_output import (
    PtransOutputSection,
    PtransSearchOutput,
    PtransOutputRoute,
    PtransOutputSpot,
    PtransOutputSectionType,
)
from prometheus.ptrans.ptrans_model import (
    TransitType,
    Node,
    Edge,
    TimeTable,
    CombusEdge,
    EntryResult,
    SearchResult,
    AdjacentDictElem,
)


STOP_FILE_PATH = "data/gtfs/stops.txt"
TRAVEL_TIME_FILE_PATH = "data/gtfs/average_travel_times.csv"
SHAPE_FILE_PATH = "data/gtfs/shapes.json"
TRIP_PAIRS_FILE_PATH = "data/gtfs/trip_pairs.json"

WALK_SPEED = 30  # メートル/分。直線距離ベースなので少し遅めにしている


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


def merge_combus_edges(combus_edges: list[CombusEdge]):
    org_node_id = combus_edges[0].org_node_id
    dst_node_id = combus_edges[-1].dst_node_id
    duration = sum(edge.duration for edge in combus_edges)
    name = combus_edges[0].name
    time_tables = combus_edges[0].time_tables

    coords = []
    for edge in combus_edges:
        edge_coords = polyline.decode(edge.shape)
        if coords:
            # 先頭が重複する場合はスキップ
            if coords[-1] == edge_coords[0]:
                coords.extend(edge_coords[1:])
            else:
                coords.extend(edge_coords)
        else:
            coords.extend(edge_coords)
    merged_shape = polyline.encode(coords)

    return CombusEdge(
        org_node_id=org_node_id,
        dst_node_id=dst_node_id,
        duration=duration,
        name=name,
        shape=merged_shape,
        time_tables=time_tables,
    )


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
    single_combus_edges = []
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
        single_combus_edges.append(
            CombusEdge(
                org_node_id=org_nodeid,
                dst_node_id=dst_nodeid,
                duration=section.duration,
                name="コミュニティバス",
                shape=section.shape,
                time_tables=time_table,
            )
        )

    combus_edges = []
    for start_index in range(len(single_combus_edges)):
        merge_target_edges = []
        for merge_count in range(len(single_combus_edges) - 1):
            target_index = start_index + merge_count
            if target_index >= len(single_combus_edges):
                target_index -= len(single_combus_edges)
            merge_target_edges.append(single_combus_edges[target_index])
            merged_edge = merge_combus_edges(merge_target_edges)
            combus_edges.append(merged_edge)
        merge_target_edges.clear()

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
    print(prev_nodes.get("START"))
    while node != "START":
        node_id_list.append(node)
        node = prev_nodes[node]
    node_id_list.append(node)  # スタートノードを追加
    return node_id_list[::-1]  # 経路を逆順にして返す


def find_next_bus_time(current_time: str, time_table: List[str]):
    """
    現在時刻と時刻表から次のバスの時刻を探す。
    """
    h, m = map(int, current_time.split(":"))
    current_minutes = h * 60 + m
    for bus_time in time_table:
        bh, bm = map(int, bus_time.split(":"))
        bus_minutes = bh * 60 + bm
        if bus_minutes > current_minutes:
            return bus_time[:5]
    raise Exception("終電に間に合う経路が見つかりませんでした。")


class PtransTracer:
    """経路確定後に時刻表を参照してトレースを行うクラス。"""

    def __init__(self) -> None:
        self.shape_dict: Dict[Tuple[str, str], str] = self._load_shape_dict(
            SHAPE_FILE_PATH
        )
        self.time_table_dict: Dict[Tuple[str, str], TimeTable] = {}
        self.node_dict: Dict[str, Node] = {}

        self.combus_shape_keys: list[Tuple[str, str]] = []
        print(">>> PtransTracerのデータロードが完了しました。")

    def set_node_dict(self, node_dict: Dict[str, Node]) -> None:
        self.node_dict: Dict[str, Node] = node_dict

    def set_time_table_dict(
        self, time_table_dict: Dict[Tuple[str, str], TimeTable]
    ) -> None:
        self.time_table_dict = time_table_dict

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
            self.combus_shape_keys.append(
                (combus_edge.org_node_id, combus_edge.dst_node_id)
            )

    def create_output_section(self, edge, current_time: str) -> PtransOutputSection:
        is_edge = isinstance(edge, Edge)

        def round_duration(duration: float):
            if duration < 1:
                return 1
            else:
                return int(duration)

        # 徒歩セクションの場合
        if is_edge and edge.transit_type == TransitType.WALK:
            rounded_duration = round_duration(edge.travel_time)
            return PtransOutputSection(
                duration=rounded_duration,
                shape="",
                start_time=current_time,
                goal_time=add_time(current_time, rounded_duration),
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
            rounded_duration = round_duration(edge.travel_time)
            return PtransOutputSection(
                duration=rounded_duration,
                shape=shape,
                start_time=start_time,
                goal_time=add_time(start_time, rounded_duration),
                name=time_table.weekday_name,  # 平日で決め打ち
                type=PtransOutputSectionType.BUS,
            )

        # コミュニティバスの場合
        shape = edge.shape
        time_table = edge.time_tables
        bus_time_list = time_table.weekday  # 平日で決め打ち
        start_time = find_next_bus_time(current_time, bus_time_list)
        rounded_duration = round_duration(edge.duration)
        return PtransOutputSection(
            duration=rounded_duration,
            shape=shape,
            start_time=start_time,
            goal_time=add_time(start_time, rounded_duration),
            name=time_table.weekday_name,  # 平日で決め打ち
            type=PtransOutputSectionType.COMBUS,
        )

    def create_sections(
        self, search_result: SearchResult, start_time: str
    ) -> List[PtransOutputSection]:
        output_section_list: List[PtransOutputSection] = []
        current_time = start_time
        for edge in search_result.sections:
            output_section = self.create_output_section(edge, current_time)
            output_section_list.append(output_section)
            current_time = output_section.goal_time
        return output_section_list

    def create_spots(self, search_result: SearchResult) -> List[PtransOutputSpot]:
        spots: List[PtransOutputSpot] = []

        for section in search_result.sections:
            bus_stop = self.node_dict[section.org_node_id]
            spots.append(PtransOutputSpot(name=bus_stop.name, coord=bus_stop.coord))
        last_bus = self.node_dict[search_result.sections[-1].dst_node_id]
        spots.append(PtransOutputSpot(name=last_bus.name, coord=last_bus.coord))

        return spots

    def trace(self, search_result: SearchResult, start_time: str) -> PtransSearchOutput:
        sections = self.create_sections(search_result, start_time)
        spots = self.create_spots(search_result)
        goal_time = sections[-1].goal_time
        duration = sub_time(start_time, goal_time)

        return PtransSearchOutput(
            PtransOutputRoute(
                start_time=start_time,
                goal_time=goal_time,
                duration=duration,
                spots=spots,
                sections=sections,
            )
        )

    def clean(self):
        for shape_key in self.combus_shape_keys:
            self.shape_dict.pop(shape_key, None)


class PtransSearcher:
    """経路探索を行い最適経路を求めるクラス。"""

    def __init__(self) -> None:
        self.node_dict: Dict[str, Node] = self._load_node_dict(STOP_FILE_PATH)
        self.edge_dict: Dict[Tuple[str, str], Edge] = self._load_edge_dict(
            TRAVEL_TIME_FILE_PATH
        )
        self.time_table_dict: Dict[Tuple[str, str], TimeTable] = (
            self._load_time_table_dict()
        )
        self.adjacent_dict: Dict[str, List[AdjacentDictElem]] = (
            self._create_adjacent_edges_dict()
        )

        self.combus_node_keys: list[str] = []
        self.combus_edge_keys: list[Tuple[str, str]] = []
        self.combus_time_table_keys: list[Tuple[str, str]] = []
        self.combus_adjacent_keys: list[Tuple[str, str]] = []
        print(">>> PtransSearcherのデータロードが完了しました。")

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
            walk_time = int(distance / WALK_SPEED)
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
                    transit_time_minute=edge.travel_time,
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
            self.combus_node_keys.append(node.node_id)
        for edge in combus_edges:
            self.edge_dict[(edge.org_node_id, edge.dst_node_id)] = Edge(
                org_node_id=edge.org_node_id,
                dst_node_id=edge.dst_node_id,
                travel_time=edge.duration,
                transit_type=TransitType.COMBUS,
            )
            self.combus_edge_keys.append((edge.org_node_id, edge.dst_node_id))
        for edge in combus_edges:
            if not self.adjacent_dict.get(edge.org_node_id):
                self.adjacent_dict[edge.org_node_id] = []
            self.adjacent_dict[edge.org_node_id].append(
                AdjacentDictElem(
                    node=self.node_dict[edge.dst_node_id],
                    transit_time_minute=edge.duration,
                    transit_type=TransitType.COMBUS,
                )
            )
            self.combus_adjacent_keys.append((edge.org_node_id, edge.dst_node_id))

        # 既存のバス停から徒歩10分いないなら徒歩エッジを追加
        for combus_node in combus_nodes:
            for node_id, node in self.node_dict.items():
                # node.coordとcombus_node.coordの型をチェック
                if not isinstance(node, Node) or not isinstance(combus_node, Node):
                    raise TypeError("node and combus_node must be Node instances")
                if node.node_id == combus_node.node_id:
                    continue
                distance_to_add_node = haversine(node.coord, combus_node.coord)
                walk_time = int(distance_to_add_node / WALK_SPEED)
                if walk_time < 10:
                    self.edge_dict[(node_id, combus_node.node_id)] = Edge(
                        org_node_id=node_id,
                        dst_node_id=combus_node.node_id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )
                    self.combus_edge_keys.append((node_id, combus_node.node_id))
                    self.edge_dict[(combus_node.node_id, node_id)] = Edge(
                        org_node_id=combus_node.node_id,
                        dst_node_id=node_id,
                        travel_time=walk_time,
                        transit_type=TransitType.WALK,
                    )
                    self.combus_edge_keys.append((combus_node.node_id, node_id))
                    self.adjacent_dict[node_id].append(
                        AdjacentDictElem(
                            node=self.node_dict[combus_node.node_id],
                            transit_time_minute=walk_time,
                            transit_type=TransitType.WALK,
                        )
                    )
                    self.combus_adjacent_keys.append((node_id, combus_node.node_id))
                    self.adjacent_dict[combus_node.node_id].append(
                        AdjacentDictElem(
                            node=node,
                            transit_time_minute=walk_time,
                            transit_type=TransitType.WALK,
                        )
                    )
                    self.combus_adjacent_keys.append(
                        (combus_node.node_id, node.node_id)
                    )

        # 時刻表
        for combus_edge in combus_edges:
            self.time_table_dict[(combus_edge.org_node_id, combus_edge.dst_node_id)] = (
                combus_edge.time_tables
            )
            self.combus_time_table_keys.append(
                (combus_edge.org_node_id, combus_edge.dst_node_id)
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

    def add_entry_results(
        self,
        start_coord: Coord,
        goal_coord: Coord,
        start_candidates: List[EntryResult],
        goal_candidates: List[EntryResult],
    ):
        """出発地->出発地最寄りバス停、目的地最寄りバス停->目的地をNodeとEdgeの一覧に追加"""
        start_node_id = "START"
        goal_node_id = "GOAL"
        self.node_dict[start_node_id] = Node(
            node_id=start_node_id,
            name="出発地",
            coord=start_coord,
        )
        self.combus_node_keys.append(start_node_id)
        self.node_dict[goal_node_id] = Node(
            node_id=goal_node_id,
            name="目的地",
            coord=goal_coord,
        )
        self.combus_node_keys.append(goal_node_id)
        for start_candidate in start_candidates:
            self.edge_dict[(start_node_id, start_candidate.node.node_id)] = Edge(
                org_node_id=start_node_id,
                dst_node_id=start_candidate.node.node_id,
                travel_time=int(start_candidate.distance / WALK_SPEED),
                transit_type=TransitType.WALK,
            )
            self.combus_edge_keys.append((start_node_id, start_candidate.node.node_id))
            self.adjacent_dict.setdefault(start_node_id, []).append(
                AdjacentDictElem(
                    node=start_candidate.node,
                    transit_time_minute=int(start_candidate.distance / WALK_SPEED),
                    transit_type=TransitType.WALK,
                )
            )
            self.combus_adjacent_keys.append(
                (start_node_id, start_candidate.node.node_id)
            )
        for goal_candidate in goal_candidates:
            self.edge_dict[(goal_candidate.node.node_id, goal_node_id)] = Edge(
                org_node_id=goal_candidate.node.node_id,
                dst_node_id=goal_node_id,
                travel_time=int(goal_candidate.distance / WALK_SPEED),
                transit_type=TransitType.WALK,
            )
            self.combus_edge_keys.append((goal_candidate.node.node_id, goal_node_id))
            self.adjacent_dict.setdefault(goal_candidate.node.node_id, []).append(
                AdjacentDictElem(
                    node=self.node_dict[goal_node_id],
                    transit_time_minute=int(goal_candidate.distance / WALK_SPEED),
                    transit_type=TransitType.WALK,
                )
            )
            self.combus_adjacent_keys.append(
                (goal_candidate.node.node_id, goal_node_id)
            )

    def clean(self) -> None:
        for node_id in self.combus_node_keys:
            self.node_dict.pop(node_id, None)
        for edge_key in self.combus_edge_keys:
            self.edge_dict.pop(edge_key, None)
        for time_table_key in self.combus_time_table_keys:
            self.time_table_dict.pop(time_table_key, None)
        for org_id, dst_id in self.combus_adjacent_keys:
            if org_id in self.adjacent_dict:
                self.adjacent_dict[org_id] = [
                    elem
                    for elem in self.adjacent_dict[org_id]
                    if elem.node.node_id != dst_id
                ]

    def search(self, start_time_str: str) -> SearchResult:
        def calc_additional_cost(prev_mode: TransitType, next_mode: TransitType) -> int:
            if prev_mode == TransitType.WALK and mode == TransitType.WALK:
                return 10000
            return 0

        def calc_wait_time(curr_time_int: int, time_table: TimeTable):
            if not time_table:
                return 0
            curr_time_int = int(curr_time_int)
            curr_time_str = convert_time_int_2_str(curr_time_int)
            next_time_table_str = find_next_bus_time(
                curr_time_str, time_table.weekday
            )  # いったん平日で決め打ち
            next_time_int = convert_time_str_2_int(next_time_table_str)
            return next_time_int - curr_time_int

        start_time_int = convert_time_str_2_int(start_time_str)
        pq: List[Tuple[float, int, TransitType]] = (
            []
        )  # ポテンシャル、ノードID、交通手段
        costs: Dict[int, float] = {}
        prev_nodes: Dict[int, int] = {}  # start空の拡散結果における、ひとつ前のノードID

        start_adjacents = self.adjacent_dict.get("START")
        for start_adjacent in start_adjacents:
            heapq.heappush(
                pq,
                (
                    start_adjacent.transit_time_minute + start_time_int,
                    start_adjacent.node.node_id,
                    TransitType.WALK,
                ),
            )
            costs[start_adjacent.node.node_id] = (
                start_adjacent.transit_time_minute + start_time_int
            )
            prev_nodes[start_adjacent.node.node_id] = "START"

        while pq:
            curr_cost, node_id, prev_mode = heapq.heappop(pq)

            if node_id == "GOAL":
                # 経路をトレースしてエッジ列に変換
                node_id_list = trace_path(prev_nodes, node_id)
                edge_list = []
                for i in range(len(node_id_list) - 1):
                    org_node_id = node_id_list[i]
                    dst_node_id = node_id_list[i + 1]
                    edge = self.edge_dict.get((org_node_id, dst_node_id))
                    edge_list.append(edge)
                return SearchResult(sections=edge_list)

            for i, adjacent_elem in enumerate(self.adjacent_dict.get(node_id, [])):
                adjacent_node_id = adjacent_elem.node.node_id
                weight = adjacent_elem.transit_time_minute
                mode = adjacent_elem.transit_type
                time_table = self.time_table_dict.get((node_id, adjacent_node_id))
                try:
                    wait_time = calc_wait_time(curr_cost, time_table)
                except Exception as e:
                    wait_time = 10000
                new_cost = (
                    curr_cost
                    + weight
                    + calc_additional_cost(prev_mode, mode)
                    + wait_time
                )
                if adjacent_node_id not in costs or new_cost < costs[adjacent_node_id]:
                    costs[adjacent_node_id] = new_cost
                    prev_nodes[adjacent_node_id] = node_id
                    heapq.heappush(pq, (new_cost, adjacent_node_id, mode))
        return None
