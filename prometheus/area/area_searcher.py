from shapely.geometry import shape
from shapely.geometry.polygon import Polygon
from dataclasses import dataclass
from pprint import pprint

from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_search_output import (
    AreaSearchOutput,
    AreaSearchResult,
    ReachableArea,
    Spot,
)
from prometheus.data_loader import (
    load_spot_list,
    load_geojson,
    load_combus_stop_dict,
    load_combus_route_dict,
    load_spot_to_stops_dict,
)
from prometheus.area.spot_type import SpotType
from prometheus.coord import Coord


@dataclass
class CombusStop:
    """
    コミュニティバスのバス停を表すクラス。
    """

    id: str = ""
    name: str = ""
    coord: Coord = None

    def to_json(self):
        return {"id": self.id, "name": self.name, "coord": self.coord.to_json()}


@dataclass
class CombusSection:
    """
    コミュニティバスのセクション（バス停からバス停まで）を表すクラス。
    """

    duration_m: float = 0.0
    distance_km: float = 0.0
    geometry: str = ""

    def to_json(self):
        return {
            "duration-m": self.duration_m,
            "distance-km": self.distance_km,
            "geometry": self.geometry,
        }


@dataclass
class CombusRoute:
    """
    コミュニティバスの経路を表すクラス。
    """

    stop_list: list[CombusStop]
    section_list: list[CombusSection]

    def to_json(self):
        return {
            "stop-list": [stop.to_json() for stop in self.stop_list],
            "section-list": [section.to_json() for section in self.section_list],
        }


def calc_target_time_limit(original_max_minute: int) -> int:
    """
    指定された最大時間から、10分刻みの最大時間を計算する。
    """
    assert original_max_minute > 0
    assert original_max_minute <= 120
    return (original_max_minute // 10) * 10


def merge_polygon(base_polygon: Polygon, append_polygon: Polygon):
    assert append_polygon
    assert base_polygon is None or base_polygon.is_valid

    if not append_polygon.is_valid:
        append_polygon = append_polygon.buffer(0)
    if base_polygon is None:
        merged_polygon = append_polygon
    else:
        merged_polygon = base_polygon.union(append_polygon)

    return merged_polygon


def calc_original_reachable_polygon(spot_list: dict, target_max_limit: int) -> Polygon:
    merged_polygon = None
    for spot in spot_list:
        geojson_dict = load_geojson(spot["id"], target_max_limit)
        geojson_obj = shape(geojson_dict)
        merged_polygon = merge_polygon(merged_polygon, geojson_obj)
    return merged_polygon


def calc_with_combus_reachable_polygon() -> Polygon:
    return None


def exec_single_spot_type(
    spot_type: SpotType, spot_list: dict, target_max_limit: int
) -> AreaSearchResult:
    """
    指定されたスポットタイプに対してエリア検索を実行する。
    """
    original_reachable_polygon = calc_original_reachable_polygon(
        spot_list, target_max_limit
    )
    with_combus_reachable_polygon = calc_with_combus_reachable_polygon()
    reachable_area = ReachableArea(
        original=original_reachable_polygon, with_comnuter=with_combus_reachable_polygon
    )

    spot_list = [
        Spot(
            coord=Coord(lat=spot["lat"], lon=spot["lon"]),
            spot_type=spot_type,
            name=spot["name"],
        )
        for spot in spot_list
    ]

    return AreaSearchResult(spots=spot_list, reachable=reachable_area)


def create_combus_route(
    stop_id_list: list[str], combus_stop_dict: dict, combus_route_dict: dict
) -> CombusRoute:
    """
    コミュニティバスの経路を作成する。
    """
    # バス停のリストを作成
    stop_list = []
    for stop_id in stop_id_list:
        stop_info = combus_stop_dict.get(stop_id)
        if not stop_info:
            # これは本当は400番エラーだがめんどいので500で返す
            raise Exception(f"存在しないバス停IDが指定されています。{stop_id}")
        stop_list.append(
            CombusStop(
                id=stop_id,
                name=stop_info["name"],
                coord=Coord(lat=stop_info["lat"], lon=stop_info["lon"]),
            )
        )

    # 区間のリストを作成
    section_list = []
    for i in range(len(stop_id_list) - 1):
        from_id = stop_id_list[i]
        to_id = stop_id_list[i + 1]
        route_info = combus_route_dict.get((from_id, to_id))
        if not route_info:
            raise Exception(
                f"指定されたバス停ペアの経路が存在しません。{from_id} -> {to_id}"
            )
        section_list.append(
            CombusSection(
                duration_m=route_info["duration_m"],
                distance_km=route_info["distance_km"],
                geometry=route_info["geometry"],
            )
        )

    # 最後のバス停から最初のバス停に戻る区間を追加
    from_id = stop_id_list[-1]
    to_id = stop_id_list[0]
    route_info = combus_route_dict.get((from_id, to_id))
    if not route_info:
        raise Exception(
            f"指定されたバス停ペアの経路が存在しません。{from_id} -> {to_id}"
        )
    section_list.append(
        CombusSection(
            duration_m=route_info["duration_m"],
            distance_km=route_info["distance_km"],
            geometry=route_info["geometry"],
        )
    )

    return CombusRoute(stop_list=stop_list, section_list=section_list)


def exec_area_search(search_input: AreaSearchInput) -> AreaSearchOutput:
    """
    到達圏検索を実行する。
    """
    # 各種データのロード
    all_spot_list = load_spot_list()
    combus_stop_dict = load_combus_stop_dict()
    combus_route_dict = load_combus_route_dict()
    spot_to_stops_dict = load_spot_to_stops_dict()

    combus_route = create_combus_route(
        search_input.combus_stops, combus_stop_dict, combus_route_dict
    )
    target_max_limit = calc_target_time_limit(search_input.max_minute)

    result_dict: dict[SpotType, AreaSearchResult] = {}
    for spot_type in search_input.target_spots:
        area_search_result = exec_single_spot_type(
            spot_type, all_spot_list[spot_type.value], target_max_limit
        )
        result_dict[spot_type] = area_search_result

    return AreaSearchOutput(result_dict=result_dict)
