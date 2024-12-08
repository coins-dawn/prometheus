import requests
import json

route_car_url = "http://localhost:3000/route/car"
route_cache_url = "http://localhost:3000/route/cache"
headers = {"Content-Type": "application/json"}
payload = {
    "stops": [
        {"coord": {"lat": 36.61095, "lon": 137.2509}, "name": "stop1"},
        {"coord": {"lat": 36.61065, "lon": 137.2145}, "name": "stop2"},
        {"coord": {"lat": 36.61303, "lon": 137.1858}, "name": "stop3"},
        {"coord": {"lat": 36.63100, "lon": 137.2149}, "name": "stop4"},
    ],
    "start_time_list": ["10:00", "11:00", "13:00"],
    "debug": False,
}


def test_route_cache():
    """/route/cacheの正常系のテスト。"""
    route_car_response = requests.post(
        route_car_url, headers=headers, data=json.dumps(payload)
    )
    route_org = route_car_response.json()["result"]
    route_id = route_org["route_id"]

    route_cache_response = requests.get(route_cache_url, params={"route_id": route_id})
    assert route_cache_response.status_code == 200
    response_data = route_cache_response.json()
    assert response_data["status"] == "OK"
    route_cache = response_data["result"]

    assert route_org["route_id"] == route_cache["route_id"]
    assert route_org["distance"] == route_cache["distance"]
    assert route_org["duration"] == route_cache["duration"]


def test_not_specified_route_id():
    """ルートIDが指定されなかった場合のテスト。"""
    route_id = "xxxxxxxxx"
    # route_id ではなく noute_id になっている
    route_cache_response = requests.get(route_cache_url, params={"noute_id": route_id})
    assert route_cache_response.status_code == 400
    response_data = route_cache_response.json()
    assert response_data["status"] == "NG"
    assert response_data["message"] == f"route_idが指定されていません。"


def test_not_exist_route_cache():
    """存在しないルートIDが指定された場合のテスト。"""
    route_id = "xxxxxxxxx"
    route_cache_response = requests.get(route_cache_url, params={"route_id": route_id})
    assert route_cache_response.status_code == 400
    response_data = route_cache_response.json()
    assert response_data["status"] == "NG"
    assert response_data["message"] == f"ルートキャッシュ{route_id}が存在しません。"
