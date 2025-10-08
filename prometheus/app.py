import pprint
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus.car.car_searcher import CarSearcher
from prometheus.car.car_input import CarSearchInput
from prometheus.utility import convert_for_json
from prometheus.car.car_visualizer import generate_car_route_kml
from prometheus.static_file_loader import (
    is_sample_request,
    load_static_area_search_response,
)
from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_searcher import exec_area_search
from prometheus.data_loader import load_spot_list
from prometheus.data_loader import load_combus_stop_list

app = Flask(__name__)
car_searcher = CarSearcher()
CORS(app)


@app.route("/", methods=["GET"])
def ping():
    """
    ヘルスチェック用エンドポイント。
    """
    return "OK"


@app.route("/combus/search", methods=["POST"])
@app.route("/search/car", methods=["POST"])  # エイリアス
def combus_search():
    """
    コミュニティバスのルートを検索する。
    """
    body = request.get_json()

    try:
        search_input = CarSearchInput(**body)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    try:
        search_output = car_searcher.search(search_input)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    # generate_car_route_kml(search_output)

    return (
        jsonify(
            {
                "status": "OK",
                "result": convert_for_json(search_output),
            }
        ),
        200,
    )


@app.route("/combus/stops", methods=["GET"])
def combus_stops():
    """
    コミュニティバスのバス停一覧を取得する。
    """
    return (
        jsonify(
            {
                "status": "OK",
                "result": load_combus_stop_list(),
            }
        ),
        200,
    )


@app.route("/area/search/sample", methods=["POST"])
@app.route("/search/area", methods=["POST"])  # エイリアス
def area_search_sample():
    """
    到達圏検索のサンプルレスポンスを返す。
    """
    body = request.get_json()

    if not is_sample_request(body):
        return jsonify({"status": "NG", "message": "Invalid request"}), 400

    return (
        jsonify(
            {
                "status": "OK",
                "result": load_static_area_search_response(),
            }
        ),
        200,
    )


@app.route("/area/search", methods=["POST"])
def area_search():
    """
    到達圏検索を実行する。
    """
    try:
        body = request.get_json()
    except Exception as e:
        return jsonify({"status": "NG", "message": f"Jsonが不正です: {str(e)}"}), 400

    try:
        search_input = AreaSearchInput(body)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    try:
        search_output = exec_area_search(search_input)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    return (
        jsonify(
            {
                "status": "OK",
                "result": search_output.to_json(),
            }
        ),
        200,
    )


@app.route("/area/spots", methods=["GET"])
def area_spots():
    """
    到達圏検索で指定可能なスポット一覧を取得する。
    """
    spot_dict = load_spot_list()
    spots = []
    for key, items in spot_dict.items():
        for item in items:
            spots.append(
                {
                    "id": item.get("id"),
                    "type": key,
                    "name": item.get("name"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                }
            )
    spot_types = [key for key in spot_dict.keys()]
    spot_list = {"types": spot_types, "spots": spots}
    return jsonify({"status": "OK", "result": spot_list}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
