import csv
import json
import heapq
from collections import defaultdict
from functools import reduce
from polyline import encode
from prometheus.coord import Coord
from prometheus.geo_utility import latlon_to_mesh, haversine
from prometheus.utility import round_half_up
from prometheus.input import SearchInput
from prometheus.output import SearchOutout, OutputRoute, OutputSection, OutputStop
from datetime import datetime, timedelta


CAR_WAY_FILE_PATH = "data/osm/car_ways.csv"
CAR_NODE_FILE_PATH = "data/osm/car_nodes.csv"

STAYTIME_PER_STOP = 1  # バス停ごとの停車時間[分]
BUS_SPEED_KM_PER_HOUR = 40  # バスのスピード[km/h]
BUS_CIRCLE_COUNT = 10  # バスが周回する数


class CarSearcher:
    def __init__(self):
        self.out_link_dict: dict[int, list[tuple[int, float]]] = defaultdict(list)
        self.link_distance_dict: dict[tuple[int, int], int] = {}
        self._load_links(CAR_WAY_FILE_PATH)
        self.node_dict = self._load_nodes(CAR_NODE_FILE_PATH)
        self.mesh_dict = self._create_mesh_dict()
        print(">>> グラフのロードが完了しました。")

    def _load_links(self, file_path: str) -> None:
        """リンクをロードする。"""
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーをスキップ
            for from_node, to_node, distance in reader:
                from_node = int(from_node)
                to_node = int(to_node)
                distance = float(distance)
                self.out_link_dict[from_node].append((to_node, distance))
                self.link_distance_dict[(from_node, to_node)] = distance

    def _load_nodes(self, file_path: str) -> dict[int, tuple[Coord, int]]:
        """ノードをロードする。"""
        node_dict: dict[int, tuple[Coord, int]] = defaultdict(tuple)
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーをスキップ
            for nodeid, lat, lon, meshid in reader:
                nodeid = int(nodeid)
                lat = float(lat)
                lon = float(lon)
                meshid = int(meshid)
                node_dict[nodeid] = (Coord(lat=lat, lon=lon), meshid)
        return node_dict

    def _create_mesh_dict(self) -> dict[int, list[tuple[int, Coord]]]:
        """メッシュIDから、そこに属するノード一覧を作成する。"""
        mesh_dict: dict[int, list[int]] = defaultdict(list)
        for nodeid, value in self.node_dict.items():
            coord, meshid = value
            if meshid not in mesh_dict:
                mesh_dict[meshid] = []
            mesh_dict[meshid].append((nodeid, coord))
        return mesh_dict

    def _find_nearest_node(self, target_coord: Coord) -> int:
        """緯度経度から最寄りノードを検索する（地点登録）"""
        mesh_id = latlon_to_mesh(target_coord)
        candidates = self.mesh_dict[mesh_id]
        min_distance = 1 << 29
        min_nodeid = None
        for nodeid, coord in candidates:
            distance = haversine(target_coord, coord)
            if distance < min_distance:
                min_distance = distance
                min_nodeid = nodeid
        return min_nodeid

    def _trace(self, route_node_sequence: list[int]) -> OutputSection:
        """ノード列をトレースしセクションの情報を詰めて返す。"""
        distance_m = 0
        coord_list: list[Coord] = []
        for next_index in range(1, len(route_node_sequence)):
            prev_idex = next_index - 1
            prev_nodeid = route_node_sequence[prev_idex]
            next_nodeid = route_node_sequence[next_index]
            link_distance = self.link_distance_dict[prev_nodeid, next_nodeid]
            distance_m += link_distance
            prev_coord, _ = self.node_dict[prev_nodeid]
            next_coord, _ = self.node_dict[next_nodeid]
            coord_list.append(prev_coord)
            if next_index == len(route_node_sequence) - 1:
                coord_list.append(next_coord)
        encoded_shape = encode([(coord.lat, coord.lon) for coord in coord_list])
        bus_speed_meter_per_minute = BUS_SPEED_KM_PER_HOUR * 1000 / 60
        duration_m = round_half_up(distance_m / bus_speed_meter_per_minute)

        return OutputSection(
            distance=round_half_up(distance_m),
            duration=duration_m,
            shape=encoded_shape,
        )

    def _dijkstra(self, start, goal, visited_global) -> tuple[OutputSection, list[int]]:
        """Dijkstraを実行し最短経路を得る。"""
        queue = [(0, start, [start])]
        visited_local = set()
        route_node_sequence = None
        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == goal:
                route_node_sequence = path
                break
            if node in visited_local:
                continue
            visited_local.add(node)
            for neighbor, weight in self.out_link_dict[node]:
                if neighbor in visited_global:
                    continue  # 折り返し禁止（訪問済ノードは使わない）
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))

        if not route_node_sequence:
            return None, None

        return self._trace(route_node_sequence), route_node_sequence

    def _find_route_through_nodes(self, node_sequence) -> list[OutputSection]:
        """指定ノード列を順番にめぐる経路を構築"""
        visited_nodes_list = []
        visited_nodes_set = set()
        output_section_list: list[OutputSection] = []
        for i in range(len(node_sequence) - 1):
            start = node_sequence[i]
            goal = node_sequence[i + 1]
            route, route_node_sequence = self._dijkstra(start, goal, visited_nodes_set)
            if route is None:
                # 行き止まりなどで折り返さざるを得ない場合のケア
                # 出発地から20ノードだけ重複を許容する
                route, route_node_sequence = self._dijkstra(
                    start, goal, visited_nodes_list[0:-20]
                )
                if route is None:
                    raise ValueError(f"経路が見つかりません: {start} → {goal}")
            # 前のゴールと重複しないようにする
            visited_nodes_list.extend(route_node_sequence[1:])
            visited_nodes_set.update(route_node_sequence[1:])
            output_section_list.append(route)
        return output_section_list

    def _calculate_departure_time_matrix(
        self, output_section_list: list[OutputSection], start_time: str
    ) -> list[list[str]]:
        start_time_obj = datetime.strptime(start_time, "%H:%M")
        total_duration = sum(section.duration + STAYTIME_PER_STOP for section in output_section_list)
        departure_times = []

        for i in range(len(output_section_list)):
            departure_times.append([])
            current_time = start_time_obj
            for j in range(BUS_CIRCLE_COUNT):
                departure_times[i].append(current_time.strftime("%H:%M"))
                current_time += timedelta(minutes=total_duration)
            if i < len(output_section_list) - 1:
                start_time_obj += timedelta(minutes=output_section_list[i].duration)

        return departure_times

    def search(self, search_input: SearchInput) -> SearchOutout:
        coord_sequence = [stop.coord for stop in search_input.stops]
        stop_node_sequence = [
            self._find_nearest_node(coord) for coord in coord_sequence
        ]
        stop_node_sequence.append(stop_node_sequence[0])  # 最後にスタート地点に戻る
        output_section_list = self._find_route_through_nodes(stop_node_sequence)
        departure_time_matrix = self._calculate_departure_time_matrix(
            output_section_list, search_input.start_time
        )
        return SearchOutout(
            route=OutputRoute(
                distance=reduce(
                    lambda acc, x: acc + x.distance, output_section_list, 0
                ),
                duration=reduce(lambda acc, x: acc + x.duration, output_section_list, 0)
                + len(search_input.stops) * STAYTIME_PER_STOP,
                stops=[
                    OutputStop(stop=stop, stay_time=STAYTIME_PER_STOP, departure_times=departure_time_matrix[i])
                    for i, stop in enumerate(search_input.stops)
                ],
                sections=output_section_list,
            )
        )

if __name__ == "__main__":
    searcher = CarSearcher()
    # Example usage
    input_str="""
{
    "route-name": "循環バス",
    "start-time": "10:00",
    "stops": [
        {
            "name": "バス停1",
            "coord": {
                "lat": 36.65742,
                "lon": 137.17421
            }
        },
        {
            "name": "バス停2",
            "coord": {
                "lat": 36.68936,
                "lon": 137.18519
            }
        },
        {
            "name": "バス停3",
            "coord": {
                "lat": 36.67738,
                "lon": 137.23892
            }
        },
        {
            "name": "バス停4",
            "coord": {
                "lat": 36.65493,
                "lon": 137.24001
            }
        },
        {
            "name": "バス停5",
            "coord": {
                "lat": 36.63964,
                "lon": 137.21958
            }
        }
    ]
}
"""
    search_input = SearchInput(**json.loads(input_str))
    result = searcher.search(search_input)
    print(result)
