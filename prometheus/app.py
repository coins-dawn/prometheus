from flask import Flask, request, jsonify
from prometheus.car_searcher import CarSearcher
from prometheus.ptrans_searcher import PtransSearcher
from prometheus.input import CarSearchInput, PtransSearchInput
from prometheus.utility import convert_for_json
from prometheus.visualize import generate_car_route_kml

app = Flask(__name__)
car_searcher = CarSearcher()
ptrans_searcher = PtransSearcher()


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
        search_input = PtransSearchInput(**body)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 400

    search_output = ptrans_searcher.search(search_input)

    # try:
    #     search_output = ptrans_searcher.search(search_input)
    # except Exception as e:
    #     return jsonify({"status": "NG", "message": str(e)}), 500

    # generate_kml(search_output)

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
