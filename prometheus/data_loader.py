import json


SPOT_LIST_FILE_PATH = "data/area/toyama_spot_list.json"
COMBUS_STOP_LIST_FILE_PATH = "data/area/combus_stops.json"
COMBUS_ROUTES_FILE_PATH = "data/area/combus_routes.json"
SPOT_TO_STOPS_FILE_PATH = "data/area/spot_to_stops.json"


def load_spot_list():
    """
    スポット一覧をロードする。
    """
    with open(SPOT_LIST_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_combus_stop_list():
    """
    コミュニティバスの一覧をロードする。
    """
    with open(COMBUS_STOP_LIST_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_combus_stop_dict():
    """
    コミュニティバスの一覧をロードしdict型式で返却する。
    """
    combus_stop_list = load_combus_stop_list()
    return {
        combus_stop["id"]: {
            "name": combus_stop["name"],
            "lat": combus_stop["lat"],
            "lon": combus_stop["lon"],
        }
        for combus_stop in combus_stop_list["combus-stops"]
    }


def load_geojson(id_str: str, max_minute: int):
    """
    指定されたIDと最大時間に対応するGeoJSONをロードする。
    """
    file_path = f"data/area/geojson/{id_str}_{max_minute}.geojson"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_combus_route_dict():
    """
    コミュニティバスの経路一覧をロードしdict型式で返却する。
    """
    combus_route_dict = {}
    combus_route_list = []
    with open(COMBUS_ROUTES_FILE_PATH, "r", encoding="utf-8") as f:
        combus_route_list = json.load(f)["combus-routes"]
    for combus_route in combus_route_list:
        from_id = combus_route["from"]
        to_id = combus_route["to"]
        combus_route_dict[(from_id, to_id)] = {
            "distance_km": float(combus_route["distance_km"]),
            "duration_m": float(combus_route["duration_m"]),
            "geometry": combus_route["geometry"],
        }
    return combus_route_dict


def load_spot_to_stops_dict():
    """
    スポットからバス停までの経路情報をロードしdict型式で返却する。
    """
    spot_to_stops_list = []
    spot_to_stops_dict = {}
    with open(SPOT_TO_STOPS_FILE_PATH, "r", encoding="utf-8") as f:
        spot_to_stops_list = json.load(f)["spot-to-stops"]

    for spot_to_stop in spot_to_stops_list:
        from_id = spot_to_stop["from"]
        to_id = spot_to_stop["to"]
        walk_distance_m = int(spot_to_stop["walk_distance_m"])
        spot_to_stops_dict[(from_id, to_id)] = {
            "duration_m": int(spot_to_stop["duration_m"]),
            "walk_distance_m": walk_distance_m,
        }
    return spot_to_stops_dict
