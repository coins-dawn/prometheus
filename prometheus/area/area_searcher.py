from shapely.geometry import shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely import make_valid

from prometheus.area.area_search_input import AreaSearchInput
from prometheus.area.area_search_output import (
    AreaSearchOutput,
    AreaSearchResult,
    ReachableArea,
    Spot,
    CombusStop,
    CombusSection,
    CombusRoute,
    AllAreaSearchOutput,
    AllAreaSearchResult,
    Route,
    RoutePair,
    RoutePoint,
    RouteSection,
)
from prometheus.data_loader import DataAccessor
from prometheus.area.spot_type import SpotType
from prometheus.coord import Coord
from prometheus.area.area_visualizer import output_visualize_data


MAX_WALK_DISTANCE_M = 1000  # 徒歩の最大距離[m]


class GeoJson:
    def __init__(
        self, polygon: MultiPolygon = None, reachable_mesh_codes: set[str] = None
    ):
        self.polygon: MultiPolygon = polygon if polygon else MultiPolygon()
        self.reachable_mesh_codes: set[str] = (
            reachable_mesh_codes if reachable_mesh_codes else set()
        )


def merge_polygon(base_polygon: MultiPolygon, append_polygon: MultiPolygon):
    assert (
        base_polygon is None or base_polygon.is_valid
    ), "マージ元のPolygonが不正です。"

    if append_polygon.is_empty:
        return base_polygon
    if not append_polygon.is_valid:
        append_polygon = make_valid(append_polygon)
    if base_polygon is None:
        merged_polygon = append_polygon
    else:
        merged_polygon = base_polygon.union(append_polygon)

    return merged_polygon


def merge_geojson(base_geojson: GeoJson, append_geojson: GeoJson):
    merged_polygon = merge_polygon(base_geojson.polygon, append_geojson.polygon)
    merged_reachable_mesh_codes = base_geojson.reachable_mesh_codes.union(
        append_geojson.reachable_mesh_codes
    )
    merged_geojson = GeoJson()
    merged_geojson.polygon = merged_polygon
    merged_geojson.reachable_mesh_codes = merged_reachable_mesh_codes
    return merged_geojson


def calc_diff_polygon(base_polygon: MultiPolygon, diff_polygon: MultiPolygon):
    assert base_polygon is None or base_polygon.is_valid, "差分元のPolygonが不正です。"

    if diff_polygon.is_empty:
        return base_polygon
    if not diff_polygon.is_valid:
        diff_polygon = make_valid(diff_polygon)
    if base_polygon is None:
        return None
    else:
        result_polygon = base_polygon.difference(diff_polygon)
        if result_polygon.geom_type == "Polygon":
            result_polygon = MultiPolygon([result_polygon])

    return result_polygon


def calc_original_reachable_geojson(
    spot_list: dict, target_max_limit: int, data_accessor: DataAccessor
) -> GeoJson:
    """
    既存の公共交通＋徒歩で到達可能な範囲を計算する。
    """
    merged_geojson = GeoJson()
    for spot in spot_list:
        geojson_dict = data_accessor.load_geojson(spot["id"], target_max_limit)
        geojson = GeoJson(
            polygon=shape(geojson_dict["geometry"]),
            reachable_mesh_codes=set(geojson_dict["properties"]["reachable-mesh"]),
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)
    return merged_geojson


def calc_with_combus_reachable_geojson_for_single_spot_and_stop(
    remaining_time: int,
    stop_index: int,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
) -> GeoJson:
    current_stop_index = stop_index
    current_remaining_time = remaining_time
    merged_geojson = GeoJson()

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
        next_geojson = GeoJson(
            polygon=shape(next_geojson_dict["geometry"]),
            reachable_mesh_codes=set(next_geojson_dict["properties"]["reachable-mesh"]),
        )
        merged_geojson = merge_geojson(merged_geojson, next_geojson)

        # 次のバス停に移動する
        current_stop_index = next_stop_index

    return merged_geojson


def calc_with_combus_reachable_geojson_for_single_spot(
    spot: dict,
    target_max_limit: int,
    spot_to_stops_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
) -> GeoJson:
    """
    特定のスポットからコミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    MAX_WALK_DISTANCE_M = 1000  # [m]
    merged_geojson = GeoJson()
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
        if walk_distance_m > MAX_WALK_DISTANCE_M:
            continue
        # 上限時間を超えている場合にはcontinue
        duration_m = value["duration_m"]
        remaining_time = target_max_limit - duration_m
        if remaining_time <= 0:
            continue
        geojson = calc_with_combus_reachable_geojson_for_single_spot_and_stop(
            remaining_time, stop_index, combus_route, data_accessor
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)
    return merged_geojson


def calc_with_combus_reachable_geojson(
    spot_list: dict,
    target_max_limit: int,
    spot_to_stops_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
) -> GeoJson:
    """
    コミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    merged_geojson = GeoJson()

    if not combus_route:
        return merged_geojson

    for spot in spot_list:
        geojson = calc_with_combus_reachable_geojson_for_single_spot(
            spot, target_max_limit, spot_to_stops_dict, combus_route, data_accessor
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)
    return merged_geojson


def calc_score(data_accessor: DataAccessor, mesh_codes: set[str]) -> int:
    mesh_dict = data_accessor.mesh_dict
    score = 0
    for mesh_code in mesh_codes:
        mesh_info = mesh_dict.get(mesh_code)
        if mesh_info:
            score += mesh_info["population"]
    return score


def filter_ref_points_in_diff_polygon(
    ref_point_list: list[dict], diff_polygon: MultiPolygon
):
    filtered_ref_points = []
    for ref_point in ref_point_list:
        point = shape(
            {
                "type": "Point",
                "coordinates": [ref_point["lon"], ref_point["lat"]],
            }
        )
        if diff_polygon.contains(point):
            filtered_ref_points.append(ref_point)
    return filtered_ref_points


def convert_to_route(route_dict: dict) -> Route:
    """
    route_dictをRouteオブジェクトに変換する。
    """
    # 出発点と到着点を取得
    first_section = route_dict["sections"][0]
    last_section = route_dict["sections"][-1]

    from_point = RoutePoint(
        name=first_section["from"]["name"],
        coord=Coord(lat=first_section["from"]["lat"], lon=first_section["from"]["lon"]),
    )

    to_point = RoutePoint(
        name=last_section["to"]["name"],
        coord=Coord(lat=last_section["to"]["lat"], lon=last_section["to"]["lon"]),
    )

    # セクションのリストを作成
    sections = []
    for section_dict in route_dict["sections"]:
        section = RouteSection(
            mode=section_dict["mode"].lower(),
            from_point=RoutePoint(
                name=section_dict["from"]["name"],
                coord=Coord(
                    lat=section_dict["from"]["lat"], lon=section_dict["from"]["lon"]
                ),
            ),
            to_point=RoutePoint(
                name=section_dict["to"]["name"],
                coord=Coord(
                    lat=section_dict["to"]["lat"], lon=section_dict["to"]["lon"]
                ),
            ),
            duration_m=section_dict["duration_m"],
            distance_m=section_dict["distance_m"],
        )
        sections.append(section)

    # 徒歩距離を計算（WALKセクションの距離の合計）
    walk_distance_m = sum(
        section_dict["distance_m"]
        for section_dict in route_dict["sections"]
        if section_dict["mode"] == "WALK"
    )

    route = Route(
        from_point=from_point,
        to_point=to_point,
        duration_m=route_dict["duration_m"],
        walk_distance_m=walk_distance_m,
        geometry=route_dict["geometry"],
        sections=sections,
    )

    return route


def calculate_original_route(
    ref_point: dict, spot_list: dict, data_accessor: DataAccessor
) -> Route:
    """
    コミュニティバスを使わない経路を返却する。
    """
    ref_point_id = ref_point["id"]
    spot_to_refpoint_dict = data_accessor.spot_to_refpoints_dict
    best_duration = 9999
    best_route = None
    for spot in spot_list:
        spot_id = spot["id"]
        route_dict = spot_to_refpoint_dict.get((spot_id, ref_point_id))
        if not route_dict:
            continue
        route: Route = convert_to_route(route_dict)
        if route.duration_m < best_duration:
            best_duration = route.duration_m
            best_route = route
    return best_route


def merge_geometry(geom1: str, geom2: str, geom3: str) -> str:
    return ""


def merge_routes(
    spot_to_stop_route: Route,
    stop_to_refpoint_route: Route,
    combus_duration: int,
    combus_geometry: str,
    combus_distance: int,
) -> Route:
    """
    3つの経路を結合して1つの経路を作成する。
    1. スポット -> 乗りバス停
    2. コミュニティバス
    3. 降りバス停 -> 目的地
    """
    sections: list[RouteSection] = []

    # スポット -> 乗りバス停
    sections.extend(spot_to_stop_route.sections)

    # コミュニティバス
    sections.append(
        RouteSection(
            mode="combus",
            from_point=stop_to_refpoint_route.from_point,
            to_point=stop_to_refpoint_route.to_point,
            duration_m=combus_duration,
            distance_m=combus_distance,
        )
    )

    # 降りバス停 -> 目的地
    sections.extend(stop_to_refpoint_route.sections)

    return Route(
        from_point=spot_to_stop_route.from_point,
        to_point=stop_to_refpoint_route.to_point,
        duration_m=spot_to_stop_route.duration_m
        + combus_duration
        + stop_to_refpoint_route.duration_m,
        walk_distance_m=spot_to_stop_route.walk_distance_m
        + stop_to_refpoint_route.walk_distance_m,
        geometry=merge_geometry(
            spot_to_stop_route.geometry,
            combus_geometry,
            stop_to_refpoint_route.geometry,
        ),
        sections=sections,
    )


def calculate_with_combus_route_for_single_spot_and_stop(
    ref_point: dict,
    spot_to_stop_route_dict: dict,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
    start_stop_index: int,
) -> Route:
    """
    コミュニティバスを利用した経路を返却する。
    1つのスポットおよび乗りバス停に対して、コミュニティバスを利用した最適な経路を探索する。
    """
    spot_to_stop_route = convert_to_route(spot_to_stop_route_dict)
    current_stop_index = start_stop_index
    combus_duration = 0

    def calc_next_stop_index(current_index: int, stop_list_size: int):
        if current_index == stop_list_size - 1:
            return 0
        return current_index + 1

    best_duration = 9999
    best_route = None
    while True:
        current_stop_index = calc_next_stop_index(
            current_stop_index, len(combus_route.stop_list)
        )
        if current_stop_index == start_stop_index:
            break
        combus_duration += combus_route.section_list[current_stop_index].duration_m
        stop_to_refpoint_route_dict = data_accessor.stop_to_refpoints_dict.get(
            (combus_route.stop_list[current_stop_index].id, ref_point["id"])
        )
        current_stop_index = current_stop_index
        if not stop_to_refpoint_route_dict:
            continue
        stop_to_refpont_route = convert_to_route(stop_to_refpoint_route_dict)
        merged_route = merge_routes(
            spot_to_stop_route,
            stop_to_refpont_route,
            combus_duration,
            "",  # geometryをちゃんとセットする
            0,  # distanceをちゃんとセットする
        )
        if merged_route.walk_distance_m > MAX_WALK_DISTANCE_M:
            continue
        if merged_route.duration_m < best_duration:
            best_duration = merged_route.duration_m
            best_route = merged_route
    return best_route


def calculate_with_combus_route_for_single_spot(
    ref_point: dict,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
    spot: dict,
) -> Route:
    """
    コミュニティバスを利用した経路を返却する。
    """
    stop_id_list = [stop.id for stop in combus_route.stop_list]

    best_duration = 9999
    best_route = None
    for key, route_dict in data_accessor.spot_to_stops_dict.items():
        spot_id, stop_id = key
        # 関係ないspotならcontinue
        if spot_id != spot["id"]:
            continue
        # コミュニティバスに含まれないバス停ならcontinue
        if stop_id not in stop_id_list:
            continue
        stop_index = stop_id_list.index(stop_id)
        # 徒歩距離がしきい値を超える場合にはcontinue
        walk_distance_m = route_dict["walk_distance_m"]
        if walk_distance_m > MAX_WALK_DISTANCE_M:
            continue
        # 上限時間を超えている場合にはcontinue
        duration_m = route_dict["duration_m"]
        remaining_time = 9999  # とりあえず大きな値を入れておく
        remaining_time -= duration_m
        if remaining_time <= 0:
            continue
        # 当該のバス停で乗る最適経路を計算
        route = calculate_with_combus_route_for_single_spot_and_stop(
            ref_point, route_dict, data_accessor, combus_route, stop_index
        )
        if route is None:
            continue
        if route.duration_m < best_duration:
            best_duration = route.duration_m
            best_route = route
    return best_route


def calculate_with_combus_route(
    ref_point: dict,
    spot_list: dict,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
) -> Route:
    """
    コミュニティバスを利用した経路を返却する。
    複数のスポットについて経路を得て、最も所要時間が短い経路を返却する。
    """
    best_duration = 9999
    best_route = None
    for spot in spot_list:
        route = calculate_with_combus_route_for_single_spot(
            ref_point, data_accessor, combus_route, spot
        )
        if route is None:
            continue
        if route.walk_distance_m > MAX_WALK_DISTANCE_M:
            continue
        if route.duration_m < best_duration:
            best_duration = route.duration_m
            best_route = route
    return best_route


def calculate_route_pairs(
    data_accessor: DataAccessor,
    diff_polygon: MultiPolygon,
    spot_list: dict,
    target_max_limit: int,
    combus_route: CombusRoute,
) -> list[RoutePair]:
    """RoutePairリストを返却する。"""
    ref_point_list = data_accessor.ref_point_list["ref-points"]
    ref_point_in_polygon = filter_ref_points_in_diff_polygon(
        ref_point_list, diff_polygon
    )

    ref_point_and_routes_list = []
    for ref_point in ref_point_in_polygon:
        original_route: Route = calculate_original_route(
            ref_point, spot_list, data_accessor
        )
        with_combus_route: Route = calculate_with_combus_route(
            ref_point, spot_list, data_accessor, combus_route
        )

        if original_route is None or with_combus_route is None:
            continue

        # originalが無効、かつwith_combusが有効なものを抽出
        original_route_is_invalid = (
            original_route.duration_m > target_max_limit
            or original_route.walk_distance_m > MAX_WALK_DISTANCE_M
        )
        if not original_route_is_invalid:
            continue
        with_combus_route_is_valid = (
            with_combus_route.duration_m <= target_max_limit
            and with_combus_route.walk_distance_m <= MAX_WALK_DISTANCE_M
        )
        if not with_combus_route_is_valid:
            continue

        ref_point_and_routes_list.append((ref_point, original_route, with_combus_route))

    # とりあえず先頭から3つ返却する
    return [
        RoutePair(original=original_route, with_combus=with_combus_route)
        for _, original_route, with_combus_route in ref_point_and_routes_list[:3]
    ]


def calculate_route_pairs_dummy() -> list[RoutePair]:
    """ダミーのRoutePairリストを返却"""
    # 出発点 / 到着点
    p_from = RoutePoint(name="出発地", coord=Coord(lat=36.7000, lon=137.2100))
    p_to = RoutePoint(name="到着地", coord=Coord(lat=36.7020, lon=137.2120))

    # オリジナル（徒歩のみ）
    sec_orig = RouteSection(
        mode="walk",
        from_point=p_from,
        to_point=p_to,
        duration_m=10,
        distance_m=800,
    )
    route_orig = Route(
        from_point=p_from,
        to_point=p_to,
        duration_m=10,
        walk_distance_m=800,
        geometry="",
        sections=[sec_orig],
    )

    # コミュニティバスあり（徒歩＋バスの区間）
    p_stop = RoutePoint(name="バス停", coord=Coord(lat=36.7010, lon=137.2110))
    sec_walk = RouteSection(
        mode="walk", from_point=p_from, to_point=p_stop, duration_m=5, distance_m=400
    )
    sec_bus = RouteSection(
        mode="bus", from_point=p_stop, to_point=p_to, duration_m=3, distance_m=600
    )
    route_with_combus = Route(
        from_point=p_from,
        to_point=p_to,
        duration_m=8,
        walk_distance_m=400,
        geometry="",
        sections=[sec_walk, sec_bus],
    )

    pair = RoutePair(original=route_orig, with_combus=route_with_combus)
    return [pair]


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
    score_max = sum(mesh["population"] for mesh in data_accessor.mesh_dict.values())
    original_reachable_geojson = calc_original_reachable_geojson(
        spot_list, target_max_limit, data_accessor
    )
    original_score = calc_score(
        data_accessor, original_reachable_geojson.reachable_mesh_codes
    )
    original_score_rate = int(original_score * 100 / score_max)
    with_combus_reachable_geojson = calc_with_combus_reachable_geojson(
        spot_list, target_max_limit, spot_to_stops_dict, combus_route, data_accessor
    )
    diff_polygon = calc_diff_polygon(
        with_combus_reachable_geojson.polygon, original_reachable_geojson.polygon
    )
    diff_reachable_meshes = (
        with_combus_reachable_geojson.reachable_mesh_codes
        - original_reachable_geojson.reachable_mesh_codes
    )
    diff_score = calc_score(data_accessor, diff_reachable_meshes)
    diff_score_rate = int(diff_score * 100 / score_max)
    reachable_area = ReachableArea(
        original=original_reachable_geojson.polygon,
        with_combus=diff_polygon,
        original_score=original_score,
        with_combus_score=diff_score,
        original_score_rate=original_score_rate,
        with_combus_score_rate=diff_score_rate,
    )

    result_spot_list = [
        Spot(
            coord=Coord(lat=spot["lat"], lon=spot["lon"]),
            spot_type=spot_type,
            name=spot["name"],
        )
        for spot in spot_list
    ]

    route_pairs = calculate_route_pairs(
        data_accessor, diff_polygon, spot_list, target_max_limit, combus_route
    )

    return AreaSearchResult(
        spots=result_spot_list, reachable=reachable_area, route_pairs=route_pairs
    )


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


def exec_area_search_all(data_accessor: DataAccessor) -> AllAreaSearchOutput:
    """
    すべての上限時間・スポットタイプで到達圏探索を実行する。
    """
    all_spot_list = data_accessor.spot_list
    time_limit_list = [time_m for time_m in range(30, 130, 10)]
    result_list: list[AllAreaSearchResult] = []
    for spot_type, spot_list in data_accessor.spot_list.items():
        for time_limit in time_limit_list:
            spot_list = all_spot_list[spot_type]
            reachable_geojson = calc_original_reachable_geojson(
                spot_list, time_limit, data_accessor
            )
            score = calc_score(data_accessor, reachable_geojson.reachable_mesh_codes)
            result_list.append(
                AllAreaSearchResult(
                    spot_type=spot_type,
                    time_limit=time_limit,
                    polygon=reachable_geojson.polygon,
                    score=score,
                )
            )
    return AllAreaSearchOutput(result_list=result_list)
