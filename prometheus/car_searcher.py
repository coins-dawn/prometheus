import pandas as pd
import simplekml
import math
from math import floor
import csv
import heapq
from collections import defaultdict

CAR_WAY_FILE_PATH = "data/osm/car_ways.csv"
CAR_NODE_FILE_PATH = "data/osm/car_nodes.csv"


def latlon_to_mesh(lat, lon):
    """3次メッシュコードを計算する。"""
    primary = floor(lat * 1.5) * 100 + floor(lon - 100)
    secondary = floor((lat * 60) % 40 / 5) * 10 + floor((lon * 60) % 60 / 7.5)
    tertiary = floor((lat * 3600) % 300 / 30) * 10 + floor((lon * 3600) % 450 / 45)

    return int(f"{primary}{secondary}{tertiary}")


def haversine(lat1, lon1, lat2, lon2):
    """2点の距離を計算する。"""
    R = 6371000  # 地球の半径 (メートル)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class CarSearcher:
    def __init__(self):
        self.graph = self.load_graph(CAR_WAY_FILE_PATH)
        self.nodes_df = pd.read_csv(CAR_NODE_FILE_PATH)
        self.mesh_dict = self.create_mesh_dict()
        print(">>> グラフのロードが完了しました。")

    def load_graph(self, file_path: str) -> defaultdict:
        """グラフをロードする。"""
        graph = defaultdict(list)
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーをスキップ
            for from_node, to_node, dist in reader:
                from_node = int(from_node)
                to_node = int(to_node)
                dist = float(dist)
                graph[from_node].append((to_node, dist))
        return graph

    def create_mesh_dict(self):
        """メッシュIDから、そこに属するノード一覧を作成する。"""
        mesh_dict = {}
        for _, row in self.nodes_df.iterrows():
            mesh_id = row["3次メッシュID"]
            if mesh_id not in mesh_dict:
                mesh_dict[mesh_id] = []
            mesh_dict[mesh_id].append(row["ノード番号"])
        return mesh_dict

    def find_nearest_node(self, lat, lon):
        """緯度経度から最寄りノードを検索する（地点登録）"""
        mesh_id = latlon_to_mesh(lat, lon)
        candidates = self.nodes_df[
            self.nodes_df["ノード番号"].isin(self.mesh_dict.get(mesh_id, []))
        ]
        if candidates.empty:
            candidates = self.nodes_df  # メッシュ内にない場合は全体から探す
        return int(
            candidates.loc[
                candidates.apply(
                    lambda row: haversine(lat, lon, row["緯度"], row["経度"]), axis=1
                ).idxmin(),
                "ノード番号",
            ]
        )

    def dijkstra(self, start, goal, visited_global):
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
            for neighbor, weight in self.graph[node]:
                if neighbor in visited_global:
                    continue  # 折り返し禁止（訪問済ノードは使わない）
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
        return None

    def find_route_through_nodes(self, node_sequence):
        """指定ノード列を順番にめぐる経路を構築"""
        full_path = []
        visited_nodes = []
        for i in range(len(node_sequence) - 1):
            start = node_sequence[i]
            goal = node_sequence[i + 1]
            path = self.dijkstra(start, goal, visited_nodes)
            if path is None:
                # 行き止まりなどで折り返さざるを得ない場合のケア
                # 出発地から20ノードだけ重複を許容する
                path = self.dijkstra(start, goal, visited_nodes[0:-20])
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


if __name__ == "__main__":
    car_searcher = CarSearcher()
    request_coords = [
        (36.65742, 137.17421),
        (36.68936, 137.18519),
        (36.67738, 137.23892),
        (36.65493, 137.24001),
        (36.63964, 137.21958),
    ]
    node_sequence = [
        car_searcher.find_nearest_node(coord[0], coord[1]) for coord in request_coords
    ]
    node_sequence.append(node_sequence[0])
    route_nodes = car_searcher.find_route_through_nodes(node_sequence)
    car_searcher.export_kml(route_nodes, node_sequence)
