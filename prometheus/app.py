from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_searcher import exec_area_search, exec_area_search_all
from prometheus.data_loader import DataAccessor
from prometheus.arrange_data import arrange_data

app = Flask(__name__)
CORS(app)
arrange_data()
data_accessor = DataAccessor()


@app.route("/", methods=["GET"])
def ping():
    """
    ヘルスチェック用エンドポイント。
    """
    return "OK"


@app.route("/combus/stops", methods=["GET"])
def combus_stops():
    """
    コミュニティバスのバス停一覧を取得する。
    """
    return (
        jsonify(
            {
                "status": "OK",
                "result": data_accessor.combus_stop_list,
            }
        ),
        200,
    )


@app.route("/combus/stop-sequences", methods=["GET"])
def combus_stop_sequences():
    """
    spot type, 上限時間ごとの最適なバス停の列を返却する。
    """
    ret_list = []
    for key, stop_sequence in data_accessor.best_combus_stop_sequence_dict.items():
        spot_type, time_limit = key
        ret_list.append(
            {
                "spot-type": spot_type,
                "time-limit": time_limit,
                "stop-sequence": stop_sequence,
            }
        )
    return jsonify({"status": "OK", "result": ret_list})


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
        search_output = exec_area_search(search_input, data_accessor)
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


@app.route("/area/search/all", methods=["GET"])
def area_search_all():
    """
    すべての上限時間・スポットタイプにおいて到達圏探索を実行する。
    """
    return (
        jsonify(
            {"status": "OK", "result": exec_area_search_all(data_accessor).to_json()}
        ),
        200,
    )


@app.route("/area/spots", methods=["GET"])
def area_spots():
    """
    到達圏検索で指定可能なスポット一覧を取得する。
    """
    spot_dict = data_accessor.spot_list
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
