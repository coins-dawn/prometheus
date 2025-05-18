from flask import Flask, jsonify
import requests

app = Flask(__name__)

POST_URL = "https://prometheus-h24i.onrender.com/search/car"
POST_BODY = {
    "route-name": "循環バス",
    "start-time": "10:00",
    "stops": [
        {
            "name": "バス停1",
            "coord": {"lat": 36.65742, "lon": 137.17421}
        },
        {
            "name": "バス停2",
            "coord": {"lat": 36.68936, "lon": 137.18519}
        },
        {
            "name": "バス停3",
            "coord": {"lat": 36.67738, "lon": 137.23892}
        },
        {
            "name": "バス停4",
            "coord": {"lat": 36.65493, "lon": 137.24001}
        },
        {
            "name": "バス停5",
            "coord": {"lat": 36.63964, "lon": 137.21958}
        }
    ]
}

@app.route("/", methods=["GET"])
def proxy_request():
    response = requests.post(POST_URL, json=POST_BODY)
    try:
        return jsonify(response.json())
    except Exception:
        return response.text, response.status_code

if __name__ == "__main__":
    app.run(host="localhost", port=3003)