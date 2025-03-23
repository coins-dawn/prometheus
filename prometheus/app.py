from flask import Flask, request, jsonify
from prometheus.car_searcher import CarSearcher
from prometheus.input import SearchInput
from prometheus.utility import convert_for_json
from prometheus.visualize import generate_kml

app = Flask(__name__)
searcher = CarSearcher()


@app.route("/search/car", methods=["POST"])
def generate_route():
    body = request.get_json()

    try:
        search_input = SearchInput(**body)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    try:
        search_output = searcher.search(search_input)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    generate_kml(search_output)

    return (
        jsonify(
            {
                "status": "OK",
                "result": convert_for_json(search_output),
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
