import csv
import heapq
import simplekml
from collections import defaultdict
from functools import reduce
from polyline import encode
from coord import Coord
from geo_utility import latlon_to_mesh, haversine
from utility import round_half_up
from input import SearchInput
from output import SearchOutout, OutputRoute, OutputSection, OutputStop


CAR_WAY_FILE_PATH = "data/osm/car_ways.csv"
CAR_NODE_FILE_PATH = "data/osm/car_nodes.csv"

STAYTIME_PER_STOP = 1  # バス停ごとの停車時間[分]
BUS_SPEED_KM_PER_HOUR = 40  # バスのスピード[km/h]


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

    def _dijkstra(self, start, goal, visited_global) -> tuple[OutputSection, list[int]]:
        """Dijkstraを実行しノード列を得る。"""
        # search
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

        # trace
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

        return (
            OutputSection(
                distance=round_half_up(distance_m),
                duration=duration_m,
                shape=encoded_shape,
            ),
            route_node_sequence,
        )

    def _find_route_through_nodes(self, node_sequence) -> list[OutputSection]:
        """指定ノード列を順番にめぐる経路を構築"""
        visited_nodes = []
        output_section_list: list[OutputSection] = []
        for i in range(len(node_sequence) - 1):
            start = node_sequence[i]
            goal = node_sequence[i + 1]
            route, route_node_sequence = self._dijkstra(start, goal, visited_nodes)
            if route is None:
                # 行き止まりなどで折り返さざるを得ない場合のケア
                # 出発地から20ノードだけ重複を許容する
                route, route_node_sequence = self._dijkstra(
                    start, goal, visited_nodes[0:-20]
                )
                if route is None:
                    raise ValueError(f"経路が見つかりません: {start} → {goal}")
            # 前のゴールと重複しないようにする
            visited_nodes.extend(route_node_sequence[1:])
            output_section_list.append(route)
        return output_section_list

    def search(self, search_input: SearchInput) -> SearchOutout:
        coord_sequence = [stop.coord for stop in search_input.stops]
        stop_node_sequence = [
            self._find_nearest_node(coord) for coord in coord_sequence
        ]
        stop_node_sequence.append(stop_node_sequence[0])  # 最後にスタート地点に戻る
        output_section_list = self._find_route_through_nodes(stop_node_sequence)
        return OutputRoute(
            distance=reduce(lambda acc, x: acc + x.distance, output_section_list, 0),
            duration=reduce(lambda acc, x: acc + x.duration, output_section_list, 0)
            + len(search_input.stops) * STAYTIME_PER_STOP,
            stops=[
                OutputStop(stop=stop, stay_time=STAYTIME_PER_STOP)
                for stop in search_input.stops
            ],
            sections=output_section_list,
        )
