import requests
import json

import pprint


url = "http://localhost:3000/route/car"
headers = {"Content-Type": "application/json"}


def test_standard():
    payload = {
        "org": {
            "coord": {"lat": 34.15646, "lon": 134.6144},
            "name": "orgname",
        },
        "dst": {
            "coord": {"lat": 34.16423, "lon": 134.6277},
            "name": "dstname",
        },
        "vias": [
            {"coord": {"lat": 34.16906, "lon": 134.6155}, "name": "via1name"},
        ],
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    pprint.pprint(response.content)
    assert response.status_code == 200
