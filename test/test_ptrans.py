import requests
import json

url = "http://localhost:3000/route/ptrans"
headers = {"Content-Type": "application/json"}


def test_route_ptrans():
    payload = {
        "org_coord": {"lat": 34.17343, "lon": 134.6264},
        "dst_coord": {"lat": 34.18884, "lon": 134.5953},
        "start_time": "2024-12-07T15:10:00",
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    assert response.status_code == 400
    # assert response.status_code == 200
    # response_data = response.json()
    # assert response_data["status"] == "OK"
    # result = response_data["result"]
