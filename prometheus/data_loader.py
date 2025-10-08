import json


SPOT_LIST_FILE_PATH = "data/area/toyama_spot_list.json"
COMBUS_STOP_LIST_FILE_PATH = "data/area/combus_stops.json"


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


def load_geojson(id_str: str, max_minute: int):
    """
    指定されたIDと最大時間に対応するGeoJSONをロードする。
    """
    file_path = f"data/area/geojson/{id_str}_{max_minute}.geojson"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
