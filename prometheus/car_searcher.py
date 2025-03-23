import pandas as pd
import csv
import heapq
from collections import defaultdict

from coord import Coord
from geo_utility import latlon_to_mesh, haversine
from input import SearchInput
from output import SearchOutout, get_sample_output


CAR_WAY_FILE_PATH = "data/osm/car_ways.csv"
CAR_NODE_FILE_PATH = "data/osm/car_nodes.csv"


class CarSearcher:
    def __init__(self):
        self.graph = self._load_graph(CAR_WAY_FILE_PATH)
        self.nodes_df = pd.read_csv(CAR_NODE_FILE_PATH)
        self.mesh_dict = self._create_mesh_dict()
        print(">>> グラフのロードが完了しました。")

    def _load_graph(self, file_path: str) -> dict[int, list[tuple[int, float]]]:
        """グラフをロードする。"""
        graph: dict[int, list[tuple[int, float]]] = defaultdict(list)
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーをスキップ
            for from_node, to_node, distance in reader:
                from_node = int(from_node)
                to_node = int(to_node)
                distance = float(distance)
                graph[from_node].append((to_node, distance))
        return graph

    def _create_mesh_dict(self) -> dict[int, list[int]]:
        """メッシュIDから、そこに属するノード一覧を作成する。"""
        mesh_dict: dict[int, list[int]] = {}
        for _, row in self.nodes_df.iterrows():
            mesh_id = row["3次メッシュID"]
            if mesh_id not in mesh_dict:
                mesh_dict[mesh_id] = []
            mesh_dict[mesh_id].append(row["ノード番号"])
        return mesh_dict

    # def find_nearest_node(self, lat, lon):
    #     """緯度経度から最寄りノードを検索する（地点登録）"""
    #     mesh_id = latlon_to_mesh(Coord(lat, lon))
    #     candidates = self.nodes_df[
    #         self.nodes_df["ノード番号"].isin(self.mesh_dict.get(mesh_id, []))
    #     ]
    #     if candidates.empty:
    #         candidates = self.nodes_df  # メッシュ内にない場合は全体から探す
    #     return int(
    #         candidates.loc[
    #             candidates.apply(
    #                 lambda row: haversine(
    #                     Coord(lat, lon), Coord(row["緯度"], row["経度"])
    #                 ),
    #                 axis=1,
    #             ).idxmin(),
    #             "ノード番号",
    #         ]
    #     )

    # def dijkstra(self, start, goal, visited_global):
    #     """Dijkstraを実行しノード列を得る。"""
    #     queue = [(0, start, [start])]
    #     visited_local = set()
    #     while queue:
    #         cost, node, path = heapq.heappop(queue)
    #         if node == goal:
    #             return path
    #         if node in visited_local:
    #             continue
    #         visited_local.add(node)
    #         for neighbor, weight in self.graph[node]:
    #             if neighbor in visited_global:
    #                 continue  # 折り返し禁止（訪問済ノードは使わない）
    #             heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    #     return None

    # def find_route_through_nodes(self, node_sequence):
    #     """指定ノード列を順番にめぐる経路を構築"""
    #     full_path = []
    #     visited_nodes = []
    #     for i in range(len(node_sequence) - 1):
    #         start = node_sequence[i]
    #         goal = node_sequence[i + 1]
    #         path = self.dijkstra(start, goal, visited_nodes)
    #         if path is None:
    #             # 行き止まりなどで折り返さざるを得ない場合のケア
    #             # 出発地から20ノードだけ重複を許容する
    #             path = self.dijkstra(start, goal, visited_nodes[0:-20])
    #             if path is None:
    #                 raise ValueError(f"経路が見つかりません: {start} → {goal}")
    #         # 前のゴールと重複しないようにする
    #         full_path.extend(path[1:] if i > 0 else path)
    #         visited_nodes.extend(path[1:])
    #     return full_path

    def search(self, search_input: SearchInput) -> SearchOutout:
        return get_sample_output()
