from shapely.geometry import shape
from shapely.geometry.multipolygon import MultiPolygon

from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_search_output import (
    AreaSearchOutput,
    AreaSearchResult,
    ReachableArea,
    Spot,
    CombusStop,
    CombusSection,
    CombusRoute,
)
from prometheus.data_loader import DataAccessor
from prometheus.area.spot_type import SpotType
from prometheus.coord import Coord
from prometheus.area.area_visualizer import output_visualize_data


def merge_polygon(base_polygon: MultiPolygon, append_polygon: MultiPolygon):
    assert (
        base_polygon is None or base_polygon.is_valid
    ), "マージ元のPolygonが不正です。"

    if append_polygon.is_empty:
        return base_polygon
    if not append_polygon.is_valid:
        append_polygon = append_polygon.buffer(0)
    if base_polygon is None:
        merged_polygon = append_polygon
    else:
        merged_polygon = base_polygon.union(append_polygon)

    return merged_polygon


def calc_diff_polygon(base_polygon: MultiPolygon, diff_polygon: MultiPolygon):
    assert base_polygon is None or base_polygon.is_valid, "差分元のPolygonが不正です。"

    if diff_polygon.is_empty:
        return base_polygon
    if not diff_polygon.is_valid:
        diff_polygon = diff_polygon.buffer(0)
    if base_polygon is None:
        return None
    else:
        result_polygon = base_polygon.difference(diff_polygon)
        if result_polygon.geom_type == "Polygon":
            result_polygon = MultiPolygon([result_polygon])

    return result_polygon


def calc_original_reachable_polygon(
    spot_list: dict, target_max_limit: int, data_accessor: DataAccessor
) -> MultiPolygon:
    """
    既存の公共交通＋徒歩で到達可能な範囲を計算する。
    """
    merged_polygon = MultiPolygon()
    for spot in spot_list:
        geojson_dict = data_accessor.load_geojson(spot["id"], target_max_limit)
        geojson_obj = shape(geojson_dict)
        merged_polygon = merge_polygon(merged_polygon, geojson_obj)
    return merged_polygon


def calc_with_combus_reachable_polygon_for_single_spot_and_stop(
    remaining_time: int,
    stop_index: int,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
):
    current_stop_index = stop_index
    current_remaining_time = remaining_time
    merged_polygon = MultiPolygon()

    def calc_next_stop_index(current_index: int, stop_list_size: int):
        if current_index == stop_list_size - 1:
            return 0
        return current_index + 1

    while True:
        # 次のバス停に移動した場合に時間が残っているか確認
        section = combus_route.section_list[current_stop_index]
        current_remaining_time -= section.duration_m
        if current_remaining_time < 10:
            break

        # 時間が残っている場合はpolygonを取得してマージする
        next_stop_index = calc_next_stop_index(
            current_stop_index, len(combus_route.stop_list)
        )
        next_stop = combus_route.stop_list[next_stop_index]
        next_geojson_dict = data_accessor.load_geojson(
            next_stop.id, current_remaining_time
        )
        next_geojson_obj = shape(next_geojson_dict)
        merged_polygon = merge_polygon(merged_polygon, next_geojson_obj)

        # 次のバス停に移動する
        current_stop_index = next_stop_index

    return merged_polygon


def calc_with_combus_reachable_polygon_for_single_spot(
    spot: dict,
    target_max_limit: int,
    spot_to_stops_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
):
    """
    特定のスポットからコミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    upper_walk_distance = 1000  # [m]
    merged_polygon = MultiPolygon()
    stop_id_list = [stop.id for stop in combus_route.stop_list]

    # NOTE
    # spot_to_stops_dictのデータ構造は効率が悪い。
    # PFに課題があるようなら、spot_id -> stop_id -> value
    # のdictでデータを保持しておくと多少は良くなるかも。
    for key, value in spot_to_stops_dict.items():
        spot_id, stop_id = key
        # 関係ないspotならcontinue
        if spot_id != spot["id"]:
            continue
        # コミュニティバスに含まれないバス停ならcontinue
        if stop_id not in stop_id_list:
            continue
        stop_index = stop_id_list.index(stop_id)
        # 徒歩距離がしきい値を超える場合にはcontinue
        walk_distance_m = value["walk_distance_m"]
        if walk_distance_m > upper_walk_distance:
            continue
        # 上限時間を超えている場合にはcontinue
        duration_m = value["duration_m"]
        remaining_time = target_max_limit - duration_m
        if remaining_time <= 0:
            continue
        polygon = calc_with_combus_reachable_polygon_for_single_spot_and_stop(
            remaining_time, stop_index, combus_route, data_accessor
        )
        merged_polygon = merge_polygon(merged_polygon, polygon)
    return merged_polygon


def calc_with_combus_reachable_polygon(
    spot_list: dict,
    target_max_limit: int,
    spot_to_stops_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
) -> MultiPolygon:
    """
    コミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    merged_polygon = MultiPolygon()

    if not combus_route:
        return merged_polygon

    for spot in spot_list:
        polygon = calc_with_combus_reachable_polygon_for_single_spot(
            spot, target_max_limit, spot_to_stops_dict, combus_route, data_accessor
        )
        merged_polygon = merge_polygon(merged_polygon, polygon)
    return merged_polygon


def exec_single_spot_type(
    spot_type: SpotType,
    spot_list: dict,
    target_max_limit: int,
    spot_to_stops_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
) -> AreaSearchResult:
    """
    指定されたスポットタイプに対してエリア検索を実行する。
    """
    original_reachable_polygon = calc_original_reachable_polygon(
        spot_list, target_max_limit, data_accessor
    )
    with_combus_reachable_polygon = calc_with_combus_reachable_polygon(
        spot_list, target_max_limit, spot_to_stops_dict, combus_route, data_accessor
    )
    diff_polygon = calc_diff_polygon(
        with_combus_reachable_polygon, original_reachable_polygon
    )
    reachable_area = ReachableArea(
        original=original_reachable_polygon, with_combus=diff_polygon
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
    if len(stop_id_list) == 0:
        return None

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


def exec_area_search(
    search_input: AreaSearchInput, data_accessor: DataAccessor
) -> AreaSearchOutput:
    """
    到達圏検索を実行する。
    """
    all_spot_list = data_accessor.spot_list
    combus_stop_dict = data_accessor.combus_stop_dict
    combus_route_dict = data_accessor.combus_route_dict
    spot_to_stops_dict = data_accessor.spot_to_stops_dict

    combus_route = create_combus_route(
        search_input.combus_stops, combus_stop_dict, combus_route_dict
    )

    result_dict: dict[SpotType, AreaSearchResult] = {}
    for spot_type in search_input.target_spots:
        area_search_result = exec_single_spot_type(
            spot_type,
            all_spot_list[spot_type.value],
            search_input.max_minute,
            spot_to_stops_dict,
            combus_route,
            data_accessor,
        )

        output_visualize_data(area_search_result, spot_type, combus_route)

        result_dict[spot_type] = area_search_result

    return AreaSearchOutput(result_dict=result_dict, combus_route=combus_route)
