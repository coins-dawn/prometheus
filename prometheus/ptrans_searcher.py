import pandas as pd
import itertools
import math
import heapq
import json
from prometheus.input import PtransSearchInput
from typing import Dict, List, Tuple

STOP_FILE_PATH = "data/gtfs/stops.txt"
TRAVEL_TIME_FILE_PATH = "data/gtfs/average_travel_times.csv"
SHAPE_FILE_PATH = "data/gtfs/shapes.json"

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


def find_nearest_stops(stops, lat, lon, k=10):
    """指定した地点に最も近いバス停をk件取得"""
    distances = {
        stop_id: haversine(lat, lon, coord[0], coord[1])
        for stop_id, coord in stops.items()
    }
    return sorted(distances, key=distances.get)[:k], distances


def dijkstra(graph, start_candidates, goal_candidates, start_distances, goal_distances):
    """Dijkstra法で最短経路を探索し、徒歩区間も考慮"""

    def calc_additional_cost(prev_mode, next_mode):
        if prev_mode == "bus" and next_mode == "bus":
            return 10
        if prev_mode == "walk" and next_mode == "bus":
            return 10
        return 0

    pq = []
    costs = {}
    prev_nodes = {}
    prev_modes = {}

    for start in start_candidates:
        heapq.heappush(
            pq, (start_distances[start] / WALK_SPEED, start, "walk")
        )  # 徒歩時間加算
        costs[start] = start_distances[start] / WALK_SPEED

    while pq:
        curr_cost, node, prev_mode = heapq.heappop(pq)

        if node in goal_candidates:
            total_cost = curr_cost + goal_distances[node] / WALK_SPEED
            path = []
            while node in prev_nodes:
                path.append(node)
                node = prev_nodes[node]
            path.append(node)
            return path[::-1], total_cost

        for neighbor, weight, mode in graph.get(node, []):
            new_cost = curr_cost + weight + calc_additional_cost(prev_mode, mode)

            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                prev_nodes[neighbor] = node
                prev_modes[neighbor] = mode
                heapq.heappush(pq, (new_cost, neighbor, mode))

    return None, float("inf")


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
        self.graph = self._build_graph(self.stops, TRAVEL_TIME_FILE_PATH)
        print(">>> GTFSグラフのロードが完了しました。")

    def _load_stops(self, stops_file: str) -> Dict[int, Tuple[float, float]]:
        """stops.txt からバス停のIDと座標を取得"""
        stops_df = pd.read_csv(stops_file)
        stops: Dict[int, Tuple[float, float]] = {}
        for _, row in stops_df.iterrows():
            stops[int(row["stop_id"])] = (float(row["stop_lat"]), float(row["stop_lon"]))
        return stops

    def _build_graph(self, stops: Dict[int, Tuple[float, float]], travel_times_file: str) -> Graph:
        """バスと徒歩の移動を含むグラフを構築"""
        graph = Graph()
        travel_df = pd.read_csv(travel_times_file)
        for _, row in travel_df.iterrows():
            graph.add_edge(
                int(row["stop_from"]),
                int(row["stop_to"]),
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

    def search(self, input: PtransSearchInput) -> Tuple[List[int], float]:
        start = input.start
        goal = input.goal
        start_candidates, start_distances = find_nearest_stops(
            self.stops, start.lat, start.lon
        )
        goal_candidates, goal_distances = find_nearest_stops(
            self.stops, goal.lat, goal.lon
        )
        best_path, best_cost = dijkstra(
            self.graph.adjacency_list,
            start_candidates,
            goal_candidates,
            start_distances,
            goal_distances,
        )
        return best_path, best_cost
