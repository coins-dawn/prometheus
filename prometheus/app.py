from flask import Flask, request, jsonify
from request import Request
from pydantic import ValidationError

app = Flask(__name__)


@app.route("/")
def ping():
    return "OK"


@app.route("/route/car", methods=["POST"])
def search_car():
    try:
        json_data = request.get_json()
        data = Request(**json_data)
        return (
            jsonify(
                {"message": "Validation succeeded", "data": data.dict(by_alias=True)}
            ),
            200,
        )
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
