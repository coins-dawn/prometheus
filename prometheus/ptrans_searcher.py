import pandas as pd
import itertools
import math
import heapq
import random
import json
import polyline
from prometheus.input import PtransSearchInput
from prometheus.output import CarOutputRoute
from prometheus.coord import Coord
from typing import Dict, List, Tuple, Optional
import simplekml

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


def find_nearest_stops(stops, target_coord: Coord, k=10):
    """指定した地点に最も近いバス停をk件取得"""
    distances = {
        stop_id: haversine(target_coord.lat, target_coord.lon, coord[0], coord[1])
        for stop_id, coord in stops.items()
    }
    return sorted(distances, key=distances.get)[:k], distances

def trace_path(
    prev_nodes: Dict[int, int], goal_node: int
) -> List[int]:
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
) -> Tuple[Optional[List[int]], float]:
    """Dijkstra法で最短経路を探索し、徒歩区間も考慮"""

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

    # スタート候補を優先度付きキューに追加
    for start in start_candidates:
        heapq.heappush(
            pq, (start_distances[start] / WALK_SPEED, start, "walk")
        )  # 徒歩時間加算
        costs[start] = start_distances[start] / WALK_SPEED

    # 探索ループ
    while pq:
        curr_cost, node, prev_mode = heapq.heappop(pq)

        # ゴール候補に到達した場合、経路をトレースして返す
        if node in goal_candidates:
            total_cost = curr_cost + goal_distances[node] / WALK_SPEED
            path = trace_path(prev_nodes, node)
            return path, total_cost

        # 隣接ノードを探索
        for neighbor, weight, mode in graph.get(node, []):
            new_cost = curr_cost + weight + calc_additional_cost(prev_mode, mode)

            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                prev_nodes[neighbor] = node
                prev_modes[neighbor] = mode
                heapq.heappush(pq, (new_cost, neighbor, mode))

    # ゴールに到達できなかった場合
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
        self.shape_dict = self._load_shape_dict(SHAPE_FILE_PATH)
        self.graph = self._build_graph(self.stops, TRAVEL_TIME_FILE_PATH)
        print(">>> GTFSグラフのロードが完了しました。")

    def _load_shape_dict(self, shape_file_path: str) -> dict[tuple[str, str], list[Coord]]:
        """shapes.jsonを読み込んで (from, to) -> [Coord, ...] のdictを返す"""
        shape_dict: dict[tuple[str, str], list[Coord]] = {}
        with open(shape_file_path, "r", encoding="utf-8") as f:
            shapes = json.load(f)
            for entry in shapes:
                org = int(entry["stop_from"])
                dst = int(entry["stop_to"])
                coords = [Coord(lat=lat, lon=lon) for lat, lon in entry["shape"]]
                shape_dict[(org, dst)] = coords
        return shape_dict

    def _load_stops(self, stops_file: str) -> Dict[int, Tuple[float, float]]:
        """stops.txt からバス停のIDと座標を取得"""
        stops_df = pd.read_csv(stops_file)
        stops: Dict[int, Tuple[float, float]] = {}
        for _, row in stops_df.iterrows():
            stops[int(row["stop_id"])] = (
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
            dst_nodeid = nodeid_list[i + 1] if i + 1 < len(nodeid_list) else nodeid_list[0]
            weight = section.duration
            graph.add_edge(org_nodeid, dst_nodeid, weight, "car")
            # ★ shape_dictに緯度経度点列を追加
            decoded = polyline.decode(section.shape)
            self.shape_dict[(org_nodeid, dst_nodeid)] = [Coord(lat=lat, lon=lon) for lat, lon in decoded]

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
            

    def search(self, input: PtransSearchInput) -> Tuple[List[int], float]:
        # CarOutputRoute をグラフに追加
        if input.car_output:
            self._add_car_output_to_graph(input.car_output.route, self.graph)

        # 探索を実行
        start = input.start
        goal = input.goal
        start_candidates, start_distances = find_nearest_stops(self.stops, start)
        goal_candidates, goal_distances = find_nearest_stops(self.stops, goal)
        best_path, best_cost = dijkstra(
            self.graph.adjacency_list,
            start_candidates,
            goal_candidates,
            start_distances,
            goal_distances,
        )
        return best_path, best_cost

def export_ptrans_kml(
    node_sequence: list,
    stops_dict: dict,
    shape_dict: dict,
    start_coord: tuple[float, float] = None,
    goal_coord: tuple[float, float] = None,
    output_path="ptrans_result.kml"
):
    kml = simplekml.Kml()

    # ★バス停ピン
    for idx, nodeid in enumerate(node_sequence):
        if nodeid not in stops_dict:
            continue
        lat, lon = stops_dict[nodeid]
        kml.newpoint(name=nodeid, coords=[(lon, lat)])

    # ★スタート・ゴールピン
    if start_coord:
        kml.newpoint(name="Start", coords=[(start_coord[1], start_coord[0])])
    if goal_coord:
        kml.newpoint(name="Goal", coords=[(goal_coord[1], goal_coord[0])])

    # ★スタート→最初のバス停
    if start_coord:
        first_stop_id = node_sequence[0]
        if first_stop_id in stops_dict:
            lat, lon = stops_dict[first_stop_id]
            kml.newlinestring(
                coords=[(start_coord[1], start_coord[0]), (lon, lat)]
            ).style.linestyle.color = simplekml.Color.red

    # ★最後のバス停→ゴール
    if goal_coord:
        last_stop_id = node_sequence[-1]
        if last_stop_id in stops_dict:
            lat, lon = stops_dict[last_stop_id]
            kml.newlinestring(
                coords=[(lon, lat), (goal_coord[1], goal_coord[0])]
            ).style.linestyle.color = simplekml.Color.red

    # ★経路線
    for i in range(len(node_sequence) - 1):
        n1 = node_sequence[i]
        n2 = node_sequence[i + 1]
        key = (n1, n2)
        if key in shape_dict:
            coords = [(c.lon, c.lat) for c in shape_dict[key]]
        else:
            # stops_dict[n1], stops_dict[n2]は(緯度, 経度)
            lat1, lon1 = stops_dict[n1]
            lat2, lon2 = stops_dict[n2]
            coords = [(lon1, lat1), (lon2, lat2)]
        line = kml.newlinestring(coords=coords)
        if str(n1).startswith("A") and str(n2).startswith("A"):
            line.style.linestyle.color = simplekml.Color.lightgreen
        else:
            line.style.linestyle.color = simplekml.Color.pink
        line.style.linestyle.width = 12  # 太め

    kml.save(output_path)


if __name__ == "__main__":
    ptrans_searcher = PtransSearcher()
    input_str = r"""
{
	"start": {
		"lat": 36.392491,
		"lon": 137.143979
	},
	"goal": {
		"lat": 36.391553,
		"lon": 137.9597
	},
	"car-output": {
		"route": {
			"distance": 26124,
			"duration": 44,
			"sections": [
				{
					"distance": 4331,
					"duration": 6,
					"shape": "avv~EgyfdYYk@e@}@Uc@iA`@e@b@y@v@{BoEU_@We@IO{CeGqDgH}FdA{AVg@J[FcDl@IBM@wA{Ci@gAgBwDsBqEIFw@n@kCSgAIiAIw@G_AESGOGGEyAM_EOkAGWCeBEq@AoAAmAEgACOA{@AG@aAEs@Aw@aCgBsFQPQNKRKQCm@y@MyASWEKEqB[mCa@iAQ}@O_Em@gDk@q@Go@B]AQCGCmCAaAAw@?G?M@I?Q?aC@}C@gB?eBKINMNQFYDc@@sDZW@m@E[Ce@D}@TgCb@OBaEx@Q@G}ACgAa@kC[kBKiA{AGC~@@VGHAp@"
				},
				{
					"distance": 6272,
					"duration": 9,
					"shape": "{||~Eg~hdYAd@CPMPWXa@d@g@t@GRoAfB{BmCgAaBw@mAGGEIDEdEaEJENMNOXPFBb@Nh@Ht@DlSHlFB?M?IhEBh@a@FsA@]jB]zAWfEw@r@MfB]FATmCRiCFo@LwAPqCTkCd@kG@_@@Y|Co^BOXeCLgBFgCFgDJcE@k@@g@BaCBqBFeEDqBBgC@g@?W@aC@eA?yA?c@@e@@uDDuARcEHuAFkABi@@O?a@AcE@eDCwF?Q?K?E@eB?cA@kE@cB?q@@s@?[@I?E?O@SBy@@s@@YHmB?}@BsABcBDqBF_FBuC@_@?a@B_BBuBLiBPoCHiANoBBk@@MLkB?GBc@AK?{A?Q?]?WCoAAcAAi@@{@?QA]?K@_ABm@F_A@YPgBLuBB_@@OXsEX_F@W@OLgBBq@XyEFoABg@B[RcCZgDIE"
				},
				{
					"distance": 3252,
					"duration": 5,
					"shape": "_pz~EilsdYuC_B[c@kBeAaAYa@Iz@}AzAwCp@@tBBzAAj@?L?L?F?hABpDFb@?|@B~ABD?H?L?v@Bz@D\\@`@B`@JLBTHNH`@ThAv@pA~@tA|@VJb@J|ANpBLt@FTBL@R@P@nAHR@bGZJAPAVEPGZMbAc@bB{@`Ac@^KVEt@KTCdBOdB]`AYd@IX?^F^R~AjAB@|AjAvBzAb@\\XVfE|Ch@Al@?vA?dB?xA?`@@N@f@NxAn@lA`@l@NCkAxB_BDMLYt@}B\\}@Fi@Am@`Ce@`Ba@"
				},
				{
					"distance": 4439,
					"duration": 7,
					"shape": "_ev~EsvsdYhCq@KgBBo@Tm@d@oAY]HEt@o@r@{@k@iBw@eCfBiArBgAhGuCdAe@fBy@r@Yh@|BHf@?^FZH\\Zf@|@tA\\f@X`@f@Z^TLVHZBP@VETk@jDfAXLHJLPXn@tA^bADT@^OnAl@R^JdAZ|@XDFNF|@pJLnBNtBRF|@XXJ|Br@QfBEl@AJANGbA?d@?J@LDRDNB@?TCNq@vASd@@hFAlCObI[xGZ?`CBR?`D{B^BpARND\\ZVRPLnAp@r@`@xAz@tD~Ab@T~@b@vDnBdBz@jDlB`HvDcA`Fu@dF}BjRiCwA"
				},
				{
					"distance": 7830,
					"duration": 12,
					"shape": "uas~EexodYhCvAi@pEhD]hD_@x@In@GjAMz@IHAl@Gz@KHrAHnAHrAXlATfAHZDT@DF`@\\Gh@EO`Ec@|PM~FAj@d@bCBZBrA@`E?L?V@LFVLHTGRDDX@pBC\\ZTpALn@BbA?j@@HhBBj@V~H?HInDAL~AHRBFJb@RFxB@nAQ|CIjAD@H@MzAe@fGCb@Eb@IdAc@vFKrACbAArD?rB@`C?lC?\\?\\AdC?H?X?hB?vB?t@@lC?rFA~E?x@@h@Bj@Ff@Hj@lEbZhClR_GrAo@N}D`AwE`AmEbA`AfHm@P]M}@KyAUyAYg@KsAg@kB{@gAi@S@y@Y_DsAKEAHAHAF{@e@]MUAUDYP[J_@@iDa@_AC{ADc@?m@Nm@\\OPkAj@kBTuACy@K]AUBYLWTS^Kb@Ud@]b@y@j@OQMII?a@Es@Gy@F}Cr@eBf@{Bp@{Dv@eBVgGDsNAoG@UAg@?aAJ}@\\iDtALx@Db@A^I\\M\\WVeDxC"
				}
			],
			"stops": [
				{
					"departure_times": [
						"10:00",
						"10:44",
						"11:28",
						"12:12",
						"12:56",
						"13:40",
						"14:24",
						"15:08",
						"15:52",
						"16:36"
					],
					"stay_time": 1,
					"stop": {
						"coord": {
							"lat": 36.65742,
							"lon": 137.17421
						},
						"name": "バス停1"
					}
				},
				{
					"departure_times": [
						"10:06",
						"10:50",
						"11:34",
						"12:18",
						"13:02",
						"13:46",
						"14:30",
						"15:14",
						"15:58",
						"16:42"
					],
					"stay_time": 1,
					"stop": {
						"coord": {
							"lat": 36.68936,
							"lon": 137.18519
						},
						"name": "バス停2"
					}
				},
				{
					"departure_times": [
						"10:15",
						"10:59",
						"11:43",
						"12:27",
						"13:11",
						"13:55",
						"14:39",
						"15:23",
						"16:07",
						"16:51"
					],
					"stay_time": 1,
					"stop": {
						"coord": {
							"lat": 36.67738,
							"lon": 137.23892
						},
						"name": "バス停3"
					}
				},
				{
					"departure_times": [
						"10:20",
						"11:04",
						"11:48",
						"12:32",
						"13:16",
						"14:00",
						"14:44",
						"15:28",
						"16:12",
						"16:56"
					],
					"stay_time": 1,
					"stop": {
						"coord": {
							"lat": 36.65493,
							"lon": 137.24001
						},
						"name": "バス停4"
					}
				},
				{
					"departure_times": [
						"10:27",
						"11:11",
						"11:55",
						"12:39",
						"13:23",
						"14:07",
						"14:51",
						"15:35",
						"16:19",
						"17:03"
					],
					"stay_time": 1,
					"stop": {
						"coord": {
							"lat": 36.63964,
							"lon": 137.21958
						},
						"name": "バス停5"
					}
				}
			]
		}
	}
}
"""
    search_input = PtransSearchInput(**json.loads(input_str))
    result = ptrans_searcher.search(search_input)
    print(result)
    # 例: result, ptrans_searcher.stops, ptrans_searcher.shape_dict を使う場合
    export_ptrans_kml(
        node_sequence=result[0],
        stops_dict=ptrans_searcher.stops,
        shape_dict=ptrans_searcher.shape_dict,
        start_coord=(search_input.start.lat, search_input.start.lon),
        goal_coord=(search_input.goal.lat, search_input.goal.lon),
        output_path="ptrans_result.kml"
    )
    