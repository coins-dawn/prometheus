import json
import sys
import random
import requests
import pickle
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

random.seed(42)

TRYAL_NUM_PER_SETTING = 100  # 一つの設定ごとの試行回数
BUS_STOP_SEQUENCE_SIZE = 6  # バス停の数


def solve_tsp(duration_matrix):
    """OR-toolsを使用して巡回セールスマン問題を解く"""
    manager = pywrapcp.RoutingIndexManager(len(duration_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def duration_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return duration_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(duration_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return None, float("inf")

    # 解の取得
    route = []
    index = routing.Start(0)
    total_distance = 0
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        total_distance += duration_matrix[manager.IndexToNode(previous_index)][
            manager.IndexToNode(index)
        ]
    route.append(manager.IndexToNode(index))
    assert route

    return route, total_distance


def create_duration_matrix(stops, duration_dict):
    """所要時間の行列を作成"""
    n = len(stops)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = duration_dict.get((stops[i], stops[j]))
                if matrix[i][j] is None:
                    return None
    return matrix


def load_combus_stops(input_combus_stops_file: str):
    with open(input_combus_stops_file, "r") as f:
        combus_stops_dict = json.load(f)
    return [combus_stop["id"] for combus_stop in combus_stops_dict["combus-stops"]]


def load_combus_duration_dict(input_combus_routes_file: str):
    with open(input_combus_routes_file, "r") as f:
        combus_routes_dict = json.load(f)
    return {
        (combus_route["from"], combus_route["to"]): combus_route["duration_m"]
        for combus_route in combus_routes_dict["combus-routes"]
    }


def load_spot_dict(input_spot_list_file: str):
    with open(input_spot_list_file, "r") as f:
        return json.load(f)


def generate_combus_stop_sequence_list(
    combus_stops: list[str],
    combus_duration_dict: dict[tuple[str, str], int],
) -> list[list[str]]:
    candidate_sequences_list = []
    while len(candidate_sequences_list) < TRYAL_NUM_PER_SETTING:
        current_stops = random.sample(combus_stops, BUS_STOP_SEQUENCE_SIZE)
        duration_matrix = create_duration_matrix(current_stops, combus_duration_dict)
        if duration_matrix is None:
            continue
        route, total_duration = solve_tsp(duration_matrix)
        sequence = [current_stops[i] for i in route[:-1]]
        candidate_sequences_list.append(sequence)
    return candidate_sequences_list


def request_to_prometheus(
    combus_stop_sequence: list[str],
    spot_id: str,
    time_limit: int,
    walk_distance_limit: int,
):
    request_body = {
        "target-spot": spot_id,
        "max-minute": time_limit,
        "max-walk-distance": walk_distance_limit,
        "combus-stops": combus_stop_sequence,
    }

    try:
        response = requests.post(
            "http://127.0.0.1:8000/area/search",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    except Exception as e:
        print("prometheusとの通信に失敗しました。")
        print(e)
        return None

    if response.status_code != 200:
        print("prometheusから返却されたステータスコードが200以外です。")
        print(response.json())
        return None

    return response.json()


def best_combus_stops(
    combus_stops: list[str],
    combus_duration_dict: dict[tuple[str, str], int],
    spot_id: str,
    time_limit: int,
    walk_distance_limit: int,
) -> list[tuple]:
    """
    複数のバス停列を試行し、以下のキーで上位3つを返す：
    キー1: len(route_pairs) が大きい（降順）
    キー2: score が大きい（降順）

    Returns:
        list[tuple]: [(combus_stop_sequence, score), ...] の上位3つ
    """
    combus_stop_sequence_list = generate_combus_stop_sequence_list(
        combus_stops, combus_duration_dict
    )

    results = []
    for i, combus_stop_sequence in enumerate(combus_stop_sequence_list):
        print(f"{i+1}/{len(combus_stop_sequence_list)}")
        response_json = request_to_prometheus(
            combus_stop_sequence, spot_id, time_limit, walk_distance_limit
        )
        if not response_json:
            continue

        route_pairs = response_json["result"]["area"]["route-pairs"]
        score = response_json["result"]["area"]["reachable"]["with-combus-score"]

        results.append(
            {
                "sequence": combus_stop_sequence,
                "score": score,
                "route_pairs_count": len(route_pairs),
            }
        )

    # キー1: len(route_pairs) 降順、キー2: score 降順でソート
    results.sort(key=lambda x: (-x["route_pairs_count"], -x["score"]))

    if not results:
        raise ValueError(
            f"有効なレスポンスが見つかりませんでした。spot_id={spot_id}, time_limit={time_limit}, walk_distance_limit={walk_distance_limit}"
        )

    # 上位3つを返す（存在しない場合は少ないものを返す）
    top_3 = results[:3]
    return [(r["sequence"], r["score"]) for r in top_3]


def write_best_combus_stop_sequences(best_combus_sequences: dict, output_path: str):
    output_data = {"best-combus-stop-sequences": []}
    for best_combus_sequence in best_combus_sequences:
        output_data["best-combus-stop-sequences"].append(best_combus_sequence)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)


def send_best_sequences_to_prometheus(best_combus_sequences: list[dict]):
    request_response_pairs = []
    for best_combus_sequence in best_combus_sequences:
        request_body = {
            "target-spot": best_combus_sequence["spot"],
            "max-minute": best_combus_sequence["time-limit-m"],
            "max-walk-distance": best_combus_sequence["walk-distance-limit-m"],
            "combus-stops": best_combus_sequence["stop-sequence"],
        }
        response_json = request_to_prometheus(
            best_combus_sequence["stop-sequence"],
            best_combus_sequence["spot"],
            best_combus_sequence["time-limit-m"],
            best_combus_sequence["walk-distance-limit-m"],
        )
        request_response_pairs.append(
            {
                "request": request_body,
                "response": response_json,
            }
        )
    return request_response_pairs


def write_request_response_pairs(pairs: list[dict], output_path: str):
    with open(output_path, "wb") as f:
        pickle.dump(pairs, f)


def main(
    input_combus_stops_file: str,
    input_combus_routes_file: str,
    input_spot_list_file: str,
    output_best_combus_stop_sequences_file: str,
    output_request_response_file: str,
):
    # データのロード
    combus_stops = load_combus_stops(input_combus_stops_file)
    combus_duration_dict = load_combus_duration_dict(input_combus_routes_file)
    spot_dict = load_spot_dict(input_spot_list_file)

    spot_list = [spot for spots in spot_dict.values() for spot in spots]
    time_limit_list = [time_m for time_m in range(30, 100, 10)]
    walk_distance_limit_list = [500, 1000]

    best_combus_stop_sequences = []
    for spot in spot_list:
        for time_limit in time_limit_list:
            for walk_distance_limit in walk_distance_limit_list:
                result_list = best_combus_stops(
                    combus_stops,
                    combus_duration_dict,
                    spot["id"],
                    time_limit,
                    walk_distance_limit,
                )
                for best_combus_stop_sequence, score in result_list:
                    best_combus_stop_sequences.append(
                        {
                            "spot": spot["id"],
                            "time-limit-m": time_limit,
                            "walk-distance-limit-m": walk_distance_limit,
                            "stop-sequence": best_combus_stop_sequence,
                            "score": score,
                        }
                    )

    request_response_pairs = send_best_sequences_to_prometheus(
        best_combus_stop_sequences
    )
    write_request_response_pairs(request_response_pairs, output_request_response_file)
    write_best_combus_stop_sequences(
        best_combus_stop_sequences, output_best_combus_stop_sequences_file
    )


if __name__ == "__main__":
    input_combus_stops_file = sys.argv[1]
    input_combus_routes_file = sys.argv[2]
    input_spot_list_file = sys.argv[3]
    output_best_combus_stop_sequences_file = sys.argv[4]
    output_request_response_file = sys.argv[5]
    main(
        input_combus_stops_file,
        input_combus_routes_file,
        input_spot_list_file,
        output_best_combus_stop_sequences_file,
        output_request_response_file,
    )
