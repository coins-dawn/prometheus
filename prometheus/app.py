from flask import Flask, request, jsonify
from car_searcher import CarSearcher
from input import SearchInput
from utility import convert_for_json

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
