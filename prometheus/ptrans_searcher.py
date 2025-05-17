import pandas as pd
import itertools
import math
import heapq
import random
import json
from prometheus.input import PtransSearchInput
from prometheus.output import CarOutputRoute
from prometheus.coord import Coord
from typing import Dict, List, Tuple, Optional

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
        self.graph = self._build_graph(self.stops, TRAVEL_TIME_FILE_PATH)
        print(">>> GTFSグラフのロードが完了しました。")

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
        previous_node = None

        # stops の緯度経度を取得
        stops_coords = [(output_stop.stop.coord.lat, output_stop.stop.coord.lon) for output_stop in car_output.stops]

        for i, section in enumerate(car_output.sections):
            # ランダムなノードIDを生成
            new_node = f"A{random.randint(1000, 9999)}"

            # セクションのスタートノードを stops[i] に対応付け
            if i < len(stops_coords):
                start_lat, start_lon = stops_coords[i]
            else:
                raise ValueError("セクションとストップの数が一致しません。")

            # セクションのゴールノードを stops[i+1] または stops[0] に対応付け
            if i + 1 < len(stops_coords):
                goal_lat, goal_lon = stops_coords[i + 1]
            else:
                goal_lat, goal_lon = stops_coords[0]  # 最後のセクションのゴールは stops[0]

            # セクションをエッジとして追加
            if previous_node is not None:
                graph.add_edge(previous_node, new_node, section.duration, "car")
            previous_node = new_node

            # 既存のノードとの徒歩エッジを追加
            for stop_id, stop_coord in self.stops.items():
                dist_to_start = haversine(stop_coord[0], stop_coord[1], start_lat, start_lon)
                dist_to_goal = haversine(stop_coord[0], stop_coord[1], goal_lat, goal_lon)

                walk_time_to_start = dist_to_start / WALK_SPEED
                walk_time_to_goal = dist_to_goal / WALK_SPEED

                if walk_time_to_start < 10:  # 最大10分以内の徒歩移動のみ追加
                    graph.add_edge(stop_id, new_node, walk_time_to_start, "walk")
                    graph.add_edge(new_node, stop_id, walk_time_to_start, "walk")

                if walk_time_to_goal < 10:  # 最大10分以内の徒歩移動のみ追加
                    graph.add_edge(stop_id, new_node, walk_time_to_goal, "walk")
                    graph.add_edge(new_node, stop_id, walk_time_to_goal, "walk")

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

if __name__ == "__main__":
    ptrans_searcher = PtransSearcher()
    input_str = r"""
{
	"start": {
		"lat": 36.413101,
		"lon": 137.104771
	},
	"goal": {
		"lat": 36.43276,
		"lon": 137.155843
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
