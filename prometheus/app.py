from flask import Flask, request, jsonify
from pydantic import ValidationError
from request import CarRequest, PtransRequest, CombinedRequest
from otp_wrapper import search_car_route, search_ptrans_route, search_combined_route
from utility import save_to_binary_file, load_from_binary_file, save_car_route_as_kml

app = Flask(__name__)


@app.route("/")
def ping():
    return "OK"


@app.route("/route/car", methods=["POST"])
def search_car():
    try:
        json_data = request.get_json()
        car_request = CarRequest(**json_data)
        car_response = search_car_route(car_request)
    except ValidationError as e:
        return jsonify({"status": "NG", "message": e.errors()}), 400
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    save_to_binary_file(car_response)
    if car_request.debug:
        save_car_route_as_kml(car_response)

    return jsonify({"status": "OK", "result": car_response.model_dump()})


@app.route("/route/cache", methods=["GET"])
def route_cache():
    route_id = request.args.get("route_id")
    if not route_id:
        return (
            jsonify({"status": "NG", "message": "route_idが指定されていません。"}),
            400,
        )

    try:
        car_response = load_from_binary_file(route_id)
    except FileNotFoundError as e:
        return (
            jsonify(
                {
                    "status": "NG",
                    "message": f"ルートキャッシュ{route_id}が存在しません。",
                }
            ),
            400,
        )
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    return jsonify({"status": "OK", "result": car_response.model_dump()})


@app.route("/route/ptrans", methods=["POST"])
def route_ptrans():
    try:
        json_data = request.get_json()
        ptrans_request = PtransRequest(**json_data)
    except ValidationError as e:
        return jsonify({"status": "NG", "message": e.errors()}), 400
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    try:
        ptrans_response = search_ptrans_route(ptrans_request)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    return jsonify({"status": "OK", "result": ptrans_response.model_dump()})


@app.route("/route/combined", methods=["POST"])
def route_combined():
    try:
        json_data = request.get_json()
        combined_request = CombinedRequest(**json_data)
    except ValidationError as e:
        return jsonify({"status": "NG", "message": e.errors()}), 400
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    use_route_id = combined_request.use_route_id
    try:
        use_route = load_from_binary_file(use_route_id)
    except FileNotFoundError as e:
        return (
            jsonify(
                {
                    "status": "NG",
                    "message": f"ルートキャッシュ{use_route_id}が存在しません。",
                }
            ),
            400,
        )
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    try:
        combined_response = search_combined_route(combined_request, use_route)
    except Exception as e:
        return jsonify({"status": "NG", "message": str(e)}), 500

    return jsonify({"status": "OK", "result": combined_response.model_dump()})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
