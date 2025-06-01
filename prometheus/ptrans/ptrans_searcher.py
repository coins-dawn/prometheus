import pandas as pd
import itertools
import math
import heapq
import random
import json
import polyline
import pprint
from prometheus.ptrans.ptrans_input import PtransSearchInput
from prometheus.car.car_output import CarOutputRoute
from prometheus.ptrans.ptrans_output import (
    PtransSearchOutput,
    PtransOutputRoute,
    PtransOutputSection,
    PtransOutputSpot,
    PtransOutputSectionType,
    PtransOutputSpotType,
)
from prometheus.utility import add_time
from prometheus.coord import Coord
from typing import Dict, List, Tuple, Optional

STOP_FILE_PATH = "data/gtfs/stops.txt"
TRAVEL_TIME_FILE_PATH = "data/gtfs/average_travel_times.csv"
SHAPE_FILE_PATH = "data/gtfs/shapes.json"
TRIP_PAIRS_FILE_PATH = "data/gtfs/trip_pairs.json"

WALK_SPEED = 50  # メートル/分。直線距離ベースなので少し遅めにしている


def haversine(lat1, lon1, lat2, lon2):
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
    return R * c * 1000  # m に変換


def find_nearest_stops(stops, target_coord: Coord, k=10):
    """指定した地点に最も近いバス停をk件取得"""
    distances = {
        stop_id: haversine(target_coord.lat, target_coord.lon, coord[0], coord[1])
        for stop_id, coord in stops.items()
    }
    return sorted(distances, key=distances.get)[:k], distances


def trace_path(prev_nodes: Dict[int, int], goal_node: int) -> List[int]:
    """ゴールノードからスタートノードまでの経路をトレース"""
    path = []
    node = goal_node
    while node in prev_nodes:
        path.append(node)
        node = prev_nodes[node]
    path.append(node)  # スタートノードを追加
    return path[::-1]  # 経路を逆順にして返す


def dijkstra(
    graph: Dict[int, List[Tuple[int, float, str]]],
    start_candidates: List[int],
    goal_candidates: List[int],
    start_distances: Dict[int, float],
    goal_distances: Dict[int, float],
) -> Tuple[Optional[List[dict]], float]:
    """Dijkstra法で最短経路を探索し、徒歩区間も考慮し、エッジ列を返す"""

    def calc_additional_cost(prev_mode: str, next_mode: str) -> int:
        if prev_mode == "bus" and next_mode == "bus":
            return 10
        if prev_mode == "walk" and next_mode == "bus":
            return 10
        return 0

    pq: List[Tuple[float, int, str]] = []
    costs: Dict[int, float] = {}
    prev_nodes: Dict[int, int] = {}
    prev_modes: Dict[int, str] = {}

    for start in start_candidates:
        heapq.heappush(
            pq, (start_distances[start] / WALK_SPEED, start, "walk")
        )
        costs[start] = start_distances[start] / WALK_SPEED

    while pq:
        curr_cost, node, prev_mode = heapq.heappop(pq)

        if node in goal_candidates:
            total_cost = curr_cost + goal_distances[node] / WALK_SPEED
            # 経路をトレースしてエッジ列に変換
            path = trace_path(prev_nodes, node)
            edge_list = []
            for i in range(len(path) - 1):
                org = path[i]
                dst = path[i + 1]
                mode = prev_modes.get(dst, "walk")  # dstに到達した時のmode
                edge_list.append({
                    "org_node": org,
                    "dst_node": dst,
                    "type": mode
                })
            return edge_list, total_cost

        for neighbor, weight, mode in graph.get(node, []):
            new_cost = curr_cost + weight + calc_additional_cost(prev_mode, mode)
            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                prev_nodes[neighbor] = node
                prev_modes[neighbor] = mode
                heapq.heappush(pq, (new_cost, neighbor, mode))

    return None, float("inf")

def find_next_bus_time(current_time, time_table):
    # current_timeを"HH:MM"から分に変換
    h, m = map(int, current_time.split(":"))
    current_minutes = h * 60 + m

    for bus_time in time_table:
        # bus_timeを"HH:MM:SS"から分に変換
        bh, bm = map(int, bus_time.split(":"))
        bus_minutes = bh * 60 + bm
        if bus_minutes > current_minutes:
            # "HH:MM:SS"のまま返す
            return bus_time[:5]  # "HH:MM"
    return None


class Graph:
    def __init__(self) -> None:
        self.adjacency_list: Dict[int, List[Tuple[int, float, str]]] = {}

    def add_edge(self, from_node: int, to_node: int, weight: float, mode: str) -> None:
        """エッジを追加する"""
        if from_node not in self.adjacency_list:
            self.adjacency_list[from_node] = []
        self.adjacency_list[from_node].append((to_node, weight, mode))

    def get_neighbors(self, node: int) -> List[Tuple[int, float, str]]:
        """指定したノードの隣接ノードを取得する"""
        return self.adjacency_list.get(node, [])

    def __repr__(self) -> str:
        """グラフの内容を文字列として表示"""
        return str(self.adjacency_list)


class PtransSearcher:
    def __init__(self) -> None:
        self.stops = self._load_stops(STOP_FILE_PATH)
        self.shape_dict = self._load_shape_dict(SHAPE_FILE_PATH)
        self.trip_pairs = self._load_trip_pairs(TRIP_PAIRS_FILE_PATH)
        self.graph = self._build_graph(self.stops, TRAVEL_TIME_FILE_PATH)
        print(">>> GTFSグラフのロードが完了しました。")

    def _load_trip_pairs(self, trip_pairs_file_path: str) -> dict[tuple[str, str], dict]:
        """trip_pairs.jsonを読み込んで (from, to) -> trip情報 のdictを返す"""
        trip_pairs: dict[tuple[str, str], dict] = {}
        with open(trip_pairs_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                org = entry["stop_from"]
                dst = entry["stop_to"]
                trip_pairs[(org, dst)] = entry["trip"]
        return trip_pairs

    def _load_shape_dict(
        self, shape_file_path: str
    ) -> dict[tuple[str, str], str]:
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

    def _load_stops(self, stops_file: str) -> Dict[str, Tuple[float, float]]:
        """stops.txt からバス停のIDと座標を取得"""
        stops_df = pd.read_csv(stops_file)
        stops: Dict[str, Tuple[float, float]] = {}
        for _, row in stops_df.iterrows():
            stops[row["stop_id"]] = (
                float(row["stop_lat"]),
                float(row["stop_lon"]),
            )
        return stops

    def _build_graph(
        self, stops: Dict[int, Tuple[float, float]], travel_times_file: str
    ) -> Graph:
        """バスと徒歩の移動を含むグラフを構築"""
        graph = Graph()
        travel_df = pd.read_csv(travel_times_file)
        for _, row in travel_df.iterrows():
            graph.add_edge(
                row["stop_from"],
                row["stop_to"],
                float(row["average_travel_time"]),
                "bus",
            )
        for stop1, stop2 in itertools.combinations(stops.keys(), 2):
            dist_m = haversine(
                stops[stop1][0], stops[stop1][1], stops[stop2][0], stops[stop2][1]
            )
            walk_time = dist_m / WALK_SPEED
            if walk_time < 10:  # 最大10分以内の徒歩移動のみ追加
                graph.add_edge(stop1, stop2, walk_time, "walk")
                graph.add_edge(stop2, stop1, walk_time, "walk")
        return graph

    def _add_car_output_to_graph(
        self, car_output: CarOutputRoute, graph: Graph
    ) -> None:
        """CarOutputRoute の経路をグラフに追加"""
        # 新しいノードIDを採番
        nodeid_list = []
        for _ in car_output.stops:
            new_nodeid = f"A{random.randint(1000, 9999)}"
            nodeid_list.append(new_nodeid)

        # CarOutputRouteの経路をエッジとしてグラフに追加
        for i, section in enumerate(car_output.sections):
            org_nodeid = nodeid_list[i]
            dst_nodeid = (
                nodeid_list[i + 1] if i + 1 < len(nodeid_list) else nodeid_list[0]
            )
            weight = section.duration
            graph.add_edge(org_nodeid, dst_nodeid, weight, "car")
            # shape_dictの更新
            self.shape_dict[(org_nodeid, dst_nodeid)] = section.shape
            # trip_pairsの更新
            self.trip_pairs[(org_nodeid, dst_nodeid)] = {
                "weekday": {
                    "name": "コミュニティバス",
                    "time_table": car_output.stops[i].departure_times,
                },
                "holiday": {
                    "name": "コミュニティバス",
                    "time_table": car_output.stops[i].departure_times,
                }
            }

        # CarOutputRouteのバス停と、グラフの既存バス停の間の徒歩エッジを追加
        for i, output_stop in enumerate(car_output.stops):
            add_node_coord = output_stop.stop.coord
            add_node_id = nodeid_list[i]
            self.stops[add_node_id] = (add_node_coord.lat, add_node_coord.lon)
            for node_id, node_coord in self.stops.items():
                dist_to_add_node = haversine(
                    node_coord[0], node_coord[1], add_node_coord.lat, add_node_coord.lon
                )
                walk_time = dist_to_add_node / WALK_SPEED
                if walk_time < 10:
                    graph.add_edge(node_id, add_node_id, walk_time, "walk")
                    graph.add_edge(add_node_id, node_id, walk_time, "walk")

    def search(self, input: PtransSearchInput) -> PtransSearchOutput:
        # CarOutputRoute をグラフに追加
        if input.car_output:
            self._add_car_output_to_graph(input.car_output.route, self.graph)

        # 探索を実行
        start = input.start
        goal = input.goal
        start_candidates, start_distances = find_nearest_stops(self.stops, start)
        goal_candidates, goal_distances = find_nearest_stops(self.stops, goal)
        best_path, duration = dijkstra(
            self.graph.adjacency_list,
            start_candidates,
            goal_candidates,
            start_distances,
            goal_distances,
        )
        
        pprint.pprint(best_path)
        
        
        ### セクションを計算する（のちほどメソッドに切り出し）
        sections = []
        current_time = input.start_time
        
        # スタートから最初のバス停までの徒歩区間を追加
        first_stop = best_path[0]["org_node"]
        first_stop_coord = self.stops[first_stop]
        start_2_first_stop_distance = int(haversine(
            input.start.lat, input.start.lon, first_stop_coord[0], first_stop_coord[1]
        ))
        start_2_first_stop_duration = int(start_2_first_stop_distance / WALK_SPEED)
        current_time = add_time(current_time, start_2_first_stop_duration)
        sections.append(
            PtransOutputSection(
                distance=start_2_first_stop_distance,
                duration=0,
                shape="",
                start_time=input.start_time,
                goal_time=current_time,
                type=PtransOutputSectionType.WALK,
                name="徒歩"
            )
        )
        # 各セクションを追加
        for section in best_path:
            org_node = section["org_node"]
            dst_node = section["dst_node"]
            mode = section["type"]
            if mode == "walk":
                sections.append(
                    PtransOutputSection(
                        distance=0,
                        duration=0,
                        shape="",
                        start_time=current_time,
                        goal_time=current_time,
                        type=PtransOutputSectionType.WALK,
                        name="徒歩"
                    )
                )
                continue
            # いったんweekdayにきめうち
            time_table = self.trip_pairs.get((org_node, dst_node), {}).get("weekday", {}).get("time_table", [])
            next_time = find_next_bus_time(current_time, time_table)
            if not next_time:
                raise Exception("最終バスを逃してしまいました")
            sections.append(
                PtransOutputSection(
                    distance=0,
                    duration=0,
                    shape=self.shape_dict.get((org_node, dst_node), ""),
                    start_time=current_time,
                    goal_time=next_time,
                    type=PtransOutputSectionType.BUS,
                    name=self.trip_pairs.get((org_node, dst_node), {}).get("weekday", {}).get("name", "")
                )
            )
            current_time = next_time
        
        # 最後のバス停からゴールまでの徒歩区間を追加

        # レスポンスを構築
        return PtransSearchOutput(
            route=PtransOutputRoute(
                start_time="",
                goal_time="",
                duration=duration,
                spots=[
                    PtransOutputSpot(
                        name="",
                        coord=Coord(lat=0, lon=0),
                        type=PtransOutputSpotType.BUS,
                        stay_time=0,
                    )
                ],
                sections=sections,
            )
        )
