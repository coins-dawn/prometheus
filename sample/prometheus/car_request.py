import requests
import json

url = "http://localhost:3000/route/car"

payload = {
    "org": {"lat": 34.15646, "lon": 134.6144},
    "dst": {"lat": 34.16423, "lon": 134.6277},
    "vias": [
        {"lat": 34.16906, "lon": 134.6155},
    ],
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
