import pprint
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus.car.car_searcher import CarSearcher
from prometheus.ptrans.ptrans_searcher import (
    PtransSearcher,
    PtransTracer,
    convert_car_route_2_combus_data,
)
from prometheus.car.car_input import CarSearchInput
from prometheus.ptrans.ptrans_input import PtransSearchInput
from prometheus.utility import convert_for_json
from prometheus.car.car_visualizer import generate_car_route_kml
from prometheus.ptrans.ptrans_visualizer import generate_ptrans_route_kml

app = Flask(__name__)
car_searcher = CarSearcher()
ptrans_searcher = PtransSearcher()
ptrans_tracer = PtransTracer()
CORS(app)


@app.route("/search/car", methods=["POST"])
def car_search():
    body = request.get_json()

    try:
        search_input = CarSearchInput(**body)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    try:
        search_output = car_searcher.search(search_input)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    generate_car_route_kml(search_output)

    return (
        jsonify(
            {
                "status": "OK",
                "result": convert_for_json(search_output),
            }
        ),
        200,
    )


@app.route("/search/ptrans", methods=["POST"])
def ptrans_search():
    body = request.get_json()

    try:
        # リクエストのパース
        search_input = PtransSearchInput(**body)

        # searcherの初期化
        car_output = search_input.car_output
        combus_edges, combus_nodes = convert_car_route_2_combus_data(car_output.route)
        ptrans_searcher.add_combus_to_search_network(combus_nodes, combus_edges)

        # 地点登録、経路探索
        start_entry_results = ptrans_searcher.find_nearest_node(search_input.start)
        goal_entry_results = ptrans_searcher.find_nearest_node(search_input.goal)
        search_result = ptrans_searcher.search(start_entry_results, goal_entry_results)

        # Tracerのセットアップ
        ptrans_tracer.set_node_dict(ptrans_searcher.node_dict)
        ptrans_tracer.add_combus_to_trace_data(combus_edges)
        trace_output = ptrans_tracer.trace(
            search_result,
            search_input.start_time,
            search_input.start,
            search_input.goal,
        )
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    generate_ptrans_route_kml(trace_output.route)

    return (
        jsonify(
            {
                "status": "OK",
                "result": convert_for_json(trace_output),
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
