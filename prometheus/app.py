from flask import Flask, request, jsonify
from pydantic import ValidationError

from request import CarRequest
from otp_wrapper import search_car_route

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

    return jsonify({"status": "OK", "result": car_response.model_dump()})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
