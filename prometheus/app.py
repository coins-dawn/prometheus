from flask import Flask, request, jsonify
from car_searcher import CarSearcher

app = Flask(__name__)
searcher = CarSearcher()

@app.route("/shortest_paths", methods=["POST"])
def generate_route():
    data = request.get_json()

    if "stops" not in data or not isinstance(data["stops"], list):
        return jsonify({"error": "Invalid input format"}), 400

    try:
        # coord を取り出して lat, lon に変換
        coords = []
        for stop in data["stops"]:
            lat_str, lon_str = stop["coord"].split(",")
            coords.append((float(lat_str.strip()), float(lon_str.strip())))

        # ノード列を取得して巡回ルートを形成
        node_sequence = [searcher.find_nearest_node(lat, lon) for lat, lon in coords]
        node_sequence.append(node_sequence[0])  # 最後にスタート地点に戻る

        route = searcher.find_route_through_nodes(node_sequence)
        
        searcher.export_kml(route, node_sequence)
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)