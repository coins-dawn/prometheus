import pandas as pd
import csv
import heapq
import simplekml
from collections import defaultdict
from coord import Coord
from geo_utility import latlon_to_mesh, haversine
from input import SearchInput
from output import SearchOutout, get_sample_output


CAR_WAY_FILE_PATH = "data/osm/car_ways.csv"
CAR_NODE_FILE_PATH = "data/osm/car_nodes.csv"


class CarSearcher:
    def __init__(self):
        self.link_dict = self._load_links(CAR_WAY_FILE_PATH)
        self.nodes_df = pd.read_csv(CAR_NODE_FILE_PATH)
        self.node_dict = self._load_nodes(CAR_NODE_FILE_PATH)
        self.mesh_dict = self._create_mesh_dict()
        print(">>> グラフのロードが完了しました。")

    def _load_links(self, file_path: str) -> dict[int, list[tuple[int, float]]]:
        """リンクをロードする。"""
        link_dict: dict[int, list[tuple[int, float]]] = defaultdict(list)
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーをスキップ
            for from_node, to_node, distance in reader:
                from_node = int(from_node)
                to_node = int(to_node)
                distance = float(distance)
                link_dict[from_node].append((to_node, distance))
        return link_dict

    def _load_nodes(self, file_path: str) -> dict[int, tuple[Coord, int]]:
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

    def _create_mesh_dict(self) -> dict[int, list[int]]:
        """メッシュIDから、そこに属するノード一覧を作成する。"""
        mesh_dict: dict[int, list[int]] = defaultdict(list)
        for nodeid, value in self.node_dict.items():
            meshid = value[1]
            if meshid not in mesh_dict:
                mesh_dict[meshid] = []
            mesh_dict[meshid].append(nodeid)
        return mesh_dict

    def _find_nearest_node(self, coord: Coord) -> int:
        """緯度経度から最寄りノードを検索する（地点登録）"""
        mesh_id = latlon_to_mesh(coord)
        candidates = self.nodes_df[
            self.nodes_df["ノード番号"].isin(self.mesh_dict.get(mesh_id, []))
        ]
        if candidates.empty:
            candidates = self.nodes_df  # メッシュ内にない場合は全体から探す
        return int(
            candidates.loc[
                candidates.apply(
                    lambda row: haversine(
                        coord, Coord(lat=row["緯度"], lon=row["経度"])
                    ),
                    axis=1,
                ).idxmin(),
                "ノード番号",
            ]
        )

    def _dijkstra(self, start, goal, visited_global) -> list[int]:
        """Dijkstraを実行しノード列を得る。"""
        queue = [(0, start, [start])]
        visited_local = set()
        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == goal:
                return path
            if node in visited_local:
                continue
            visited_local.add(node)
            for neighbor, weight in self.link_dict[node]:
                if neighbor in visited_global:
                    continue  # 折り返し禁止（訪問済ノードは使わない）
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
        return None

    def find_route_through_nodes(self, node_sequence) -> list[int]:
        """指定ノード列を順番にめぐる経路を構築"""
        full_path = []
        visited_nodes = []
        for i in range(len(node_sequence) - 1):
            start = node_sequence[i]
            goal = node_sequence[i + 1]
            path = self._dijkstra(start, goal, visited_nodes)
            if path is None:
                # 行き止まりなどで折り返さざるを得ない場合のケア
                # 出発地から20ノードだけ重複を許容する
                path = self._dijkstra(start, goal, visited_nodes[0:-20])
                if path is None:
                    raise ValueError(f"経路が見つかりません: {start} → {goal}")
            # 前のゴールと重複しないようにする
            full_path.extend(path[1:] if i > 0 else path)
            visited_nodes.extend(path[1:])
        return full_path

    def export_kml(self, route_nodes, node_sequence, output_file="route.kml"):
        kml = simplekml.Kml()

        # 経路のライン
        line_coords = []
        for node_id in route_nodes:
            node = self.nodes_df[self.nodes_df["ノード番号"] == node_id]
            if node.empty:
                continue
            lat = node["緯度"].values[0]
            lon = node["経度"].values[0]
            line_coords.append((lon, lat))

        # 赤の太いライン
        linestring = kml.newlinestring(name="経路")
        linestring.coords = line_coords
        linestring.style.linestyle.color = simplekml.Color.red
        linestring.style.linestyle.width = 5  # 太さ

        # ピンの追加（訪問ノードのみ）
        for idx, node_id in enumerate(node_sequence):
            node = self.nodes_df[self.nodes_df["ノード番号"] == node_id]
            if node.empty:
                continue
            lat = node["緯度"].values[0]
            lon = node["経度"].values[0]
            pnt = kml.newpoint(name=f"目的地 {idx+1}", coords=[(lon, lat)])
            pnt.style.labelstyle.scale = 1.2
            pnt.style.iconstyle.icon.href = (
                "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
            )

        # ファイル保存
        kml.save(output_file)
        print(f">>> KMLファイルを出力しました: {output_file}")

    def search(self, search_input: SearchInput) -> SearchOutout:
        coord_sequence = [stop.coord for stop in search_input.stops]
        node_sequence = [self._find_nearest_node(coord) for coord in coord_sequence]
        node_sequence.append(node_sequence[0])  # 最後にスタート地点に戻る
        route = self.find_route_through_nodes(node_sequence)
        self.export_kml(route, node_sequence)
        return route

        # return get_sample_output()
