import json
from shapely.geometry import shape
from shapely.geometry.polygon import Polygon

from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_search_output import (
    AreaSearchOutput,
    AreaSearchResult,
    ReachableArea,
    Spot
)
from prometheus.area.spot_type import SpotType
from prometheus.coord import Coord


SPOT_LIST_FILE_PATH = "data/area/toyama_spot_list.json"


def load_spot_list(file_path: str):
    """
    スポット一覧をロードする。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calc_target_time_limit(original_max_minute: int) -> int:
    """
    指定された最大時間から、10分刻みの最大時間を計算する。
    """
    assert original_max_minute > 0
    assert original_max_minute <= 120
    return (original_max_minute // 10) * 10


def load_geojson(id_str: str, max_minute: int):
    """
    指定されたIDと最大時間に対応するGeoJSONをロードする。
    """
    file_path = f"data/area/geojson/{id_str}_{max_minute}.geojson"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def exec_single_spot_type(
    spot_type: SpotType, all_spot_list: dict, target_max_limit: int
) -> AreaSearchResult:
    """
    指定されたスポットタイプに対してエリア検索を実行する。
    """
    spot_list = all_spot_list.get(spot_type.value, [])
    polygon = Polygon()
    for spot in spot_list:
        geojson_dict = load_geojson(spot["id"], target_max_limit)
        geojson_obj = shape(geojson_dict)
        polygon = polygon.union(geojson_obj)
    reachable_area = ReachableArea(original=polygon, with_comnuter=None)
    spot_list = [
        Spot(
            coord=Coord(lat=spot["lat"], lon=spot["lon"]),
            spot_type=spot_type,
            name=spot["name"],
        )
        for spot in spot_list
    ]
    return AreaSearchResult(spots=spot_list, reachable=reachable_area)


def exec_area_search(search_input: AreaSearchInput) -> AreaSearchOutput:
    """
    到達圏検索を実行する。
    """
    target_max_limit = calc_target_time_limit(search_input.max_minute)
    all_spot_list = load_spot_list(SPOT_LIST_FILE_PATH)
    result_dict: dict[SpotType, AreaSearchResult] = {}
    for spot_type in search_input.target_spots:
        area_search_result = exec_single_spot_type(
            spot_type, all_spot_list, target_max_limit
        )
        result_dict[spot_type] = area_search_result
    return AreaSearchOutput(result_dict=result_dict)
