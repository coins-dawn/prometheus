import polyline
import math
from shapely.geometry import shape, Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely import make_valid
from dataclasses import dataclass

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


@dataclass
class WithCombusRouteSummary:
    spot_id: str
    enter_combus_stop_id: str
    exit_combus_stop_id: str
    ref_point_id: str
    duration_m: int
    walk_distance_m: int


def _to_multipolygon(geom) -> MultiPolygon:
    """
    任意のShapelyジオメトリを MultiPolygon に正規化する。
    - Polygon は [Polygon] で包む
    - GeometryCollection は再帰的に Polygon/MultiPolygon だけ抽出
    - LineString などは破棄
    """
    if geom is None:
        return MultiPolygon()
    g = geom
    # invalidなら make_valid（GeometryCollection になることがある）
    if hasattr(g, "is_valid") and not g.is_valid:
        g = make_valid(g)

    if isinstance(g, MultiPolygon):
        return g
    if isinstance(g, Polygon):
        return MultiPolygon([g])
    if getattr(g, "geom_type", "") == "GeometryCollection":
        polys = []
        for sub in g.geoms:
            mp = _to_multipolygon(sub)
            if not mp.is_empty:
                polys.extend(list(mp.geoms))
        return MultiPolygon(polys) if polys else MultiPolygon()
    # それ以外（LineString 等）は無視
    return MultiPolygon()


def merge_polygon(base_polygon: MultiPolygon, append_polygon: MultiPolygon):
    """
    2つの面ジオメトリをマージし、常に MultiPolygon を返す。
    LineString 等が混ざっても破棄して面のみを対象にする。
    """
    base = (
        _to_multipolygon(base_polygon) if base_polygon is not None else MultiPolygon()
    )
    add = _to_multipolygon(append_polygon)

    if add.is_empty:
        return base
    if base.is_empty:
        return add

    merged = base.union(add)
    return _to_multipolygon(merged)


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
    """
    差分を取り、常に MultiPolygon を返す。
    """
    base = (
        _to_multipolygon(base_polygon) if base_polygon is not None else MultiPolygon()
    )
    diff = _to_multipolygon(diff_polygon)

    if base.is_empty:
        return MultiPolygon()
    if diff.is_empty:
        return base

    result = base.difference(diff)
    return _to_multipolygon(result)


def calc_original_reachable_geojson(
    spot_list: dict,
    target_max_limit: int,
    target_max_walking_distance_m: int,
    data_accessor: DataAccessor,
    start_time: str,
) -> GeoJson:
    """
    既存の公共交通＋徒歩で到達可能な範囲を計算する。
    """
    merged_geojson = GeoJson()
    for spot in spot_list:
        geojson_dict = data_accessor.load_geojson(
            spot["id"], target_max_limit, target_max_walking_distance_m, start_time
        )
        poly = _to_multipolygon(shape(geojson_dict["geometry"]))
        geojson = GeoJson(
            polygon=poly,
            reachable_mesh_codes=set(geojson_dict["properties"]["reachable-mesh"]),
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)
    return merged_geojson


def calc_with_combus_reachable_geojson_for_single_spot_and_stop(
    remaining_time: int,
    remaining_walking_distance: int,
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
        section = combus_route.section_list[current_stop_index]
        current_remaining_time -= section.duration_m
        if current_remaining_time < 10:
            break

        next_stop_index = calc_next_stop_index(
            current_stop_index, len(combus_route.stop_list)
        )
        next_stop = combus_route.stop_list[next_stop_index]
        # NOTE
        # コミュニティバスのバス停からの到達圏ポリゴンを取得する際は
        # 出発時刻を10時に固定する
        next_geojson_dict = data_accessor.load_geojson(
            next_stop.id, current_remaining_time, remaining_walking_distance, "1000"
        )
        if next_geojson_dict:
            poly = _to_multipolygon(shape(next_geojson_dict["geometry"]))
            next_geojson = GeoJson(
                polygon=poly,
                reachable_mesh_codes=set(
                    next_geojson_dict["properties"]["reachable-mesh"]
                ),
            )
            merged_geojson = merge_geojson(merged_geojson, next_geojson)

        current_stop_index = next_stop_index

    return merged_geojson


def calc_with_combus_reachable_geojson_for_single_spot(
    spot: dict,
    target_max_limit: int,
    target_max_walking_distance_m: int,
    spot_to_spot_summary_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
    target_start_time: str,
) -> GeoJson:
    """
    特定のスポットからコミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    merged_geojson = GeoJson()
    stop_id_list = [stop.id for stop in combus_route.stop_list]

    # NOTE
    # spot_to_stops_dictのデータ構造は効率が悪い。
    # PFに課題があるようなら、spot_id -> stop_id -> value
    # のdictでデータを保持しておくと多少は良くなるかも。
    for key, summary in spot_to_spot_summary_dict.items():
        duration_m, walk_distance_m = summary
        spot_id, stop_id, start_time_key = key
        # 関係ないspotならcontinue
        if spot_id != spot["id"]:
            continue
        # 時刻が一致していなければcontinue
        if target_start_time != start_time_key:
            continue
        # コミュニティバスに含まれないバス停ならcontinue
        if stop_id not in stop_id_list:
            continue
        stop_index = stop_id_list.index(stop_id)
        # 徒歩距離がしきい値を超える場合にはcontinue
        remaining_walking_distance = target_max_walking_distance_m - walk_distance_m
        if remaining_walking_distance <= 0:
            continue
        # 上限時間を超えている場合にはcontinue
        remaining_time = target_max_limit - duration_m
        if remaining_time <= 0:
            continue
        geojson = calc_with_combus_reachable_geojson_for_single_spot_and_stop(
            remaining_time,
            remaining_walking_distance,
            stop_index,
            combus_route,
            data_accessor,
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)
    return merged_geojson


def calc_with_combus_reachable_geojson(
    spot_list: dict,
    target_max_limit: int,
    target_max_walking_distance_m: int,
    spot_to_spot_summary_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
    start_time: str,
) -> GeoJson:
    """
    コミュニティバスを利用した場合に到達可能な範囲を検索する。
    """
    merged_geojson = GeoJson()

    if not combus_route:
        return merged_geojson

    for spot in spot_list:
        geojson = calc_with_combus_reachable_geojson_for_single_spot(
            spot,
            target_max_limit,
            target_max_walking_distance_m,
            spot_to_spot_summary_dict,
            combus_route,
            data_accessor,
            start_time,
        )
        merged_geojson = merge_geojson(merged_geojson, geojson)

    # 返却前に型を保証
    assert (
        merged_geojson.polygon.geom_type == "MultiPolygon"
    ), f"merged_geojson.polygon の型が不正: {merged_geojson.polygon.geom_type}"
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
            geometry=section_dict["geometry"],
        )
        sections.append(section)

    # 徒歩距離を計算（WALKセクションの距離の合計）
    walk_distance_m = sum(
        section_dict["distance_m"]
        for section_dict in route_dict["sections"]
        if section_dict["mode"] == "WALK"
    )

    # 距離を合計
    total_distance_m = sum(
        section_dict["distance_m"] for section_dict in route_dict["sections"]
    )

    route = Route(
        from_point=from_point,
        to_point=to_point,
        duration_m=route_dict["duration_m"],
        walk_distance_m=walk_distance_m,
        geometry=route_dict["geometry"],
        sections=sections,
        distance_m=total_distance_m,
    )

    return route


def calculate_original_route(
    ref_point: dict, spot_list: dict, data_accessor: DataAccessor, start_time: str
) -> Route:
    """
    コミュニティバスを使わない経路を返却する。
    """
    ref_point_id = ref_point["id"]
    spot_to_refpoint_dict = data_accessor.spot_to_spot_summary_dict
    best_duration = 9999
    best_key_pair = None
    for spot in spot_list:
        spot_id = spot["id"]
        result = spot_to_refpoint_dict.get((spot_id, ref_point_id, start_time))
        if result is None:
            print(spot_id, ref_point_id, start_time)
            continue
        duration_m, _ = result
        if duration_m < best_duration:
            best_duration = duration_m
            best_key_pair = (spot_id, ref_point_id)
    route: Route = convert_to_route(
        data_accessor.load_route(best_key_pair[0], best_key_pair[1], start_time),
    )
    return route


def merge_geometry(geom1: str, geom2: str) -> str:
    """
    geom1, geom2 は Google polyline 形式の文字列。
    polyline ライブラリでデコード -> 連結 -> エンコードして返却する。
    """
    coords: list[tuple] = []
    if geom1:
        try:
            coords.extend(polyline.decode(geom1))
        except Exception:
            pass
    if geom2:
        try:
            coords.extend(polyline.decode(geom2))
        except Exception:
            pass
    if not coords:
        return ""
    return polyline.encode(coords)


def calculate_with_combus_route_summary_for_single_spot_and_stop(
    ref_point: dict,
    spot_to_enter_stop_duration_m: int,
    spot_to_enter_stop_walk_distance_m: int,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
    start_stop_index: int,
    spot_id: str,
) -> WithCombusRouteSummary:
    """
    コミュニティバスを利用した経路サマリーを返却する。
    1つのスポットおよび乗りバス停に対して、コミュニティバスを利用した最適な経路を探索する。
    """

    def calc_next_stop_index(current_index: int, stop_list_size: int):
        if current_index == stop_list_size - 1:
            return 0
        return current_index + 1

    current_stop_index = start_stop_index
    combus_duration = 0
    best_duration = 9999
    best_route_summary = None
    while True:
        current_stop_index = calc_next_stop_index(
            current_stop_index, len(combus_route.stop_list)
        )
        if current_stop_index == start_stop_index:
            break
        combus_duration += combus_route.section_list[current_stop_index].duration_m
        # NOTE
        # コミュニティバスのバス停から目的地への経路サマリーを取得する際は
        # 出発時刻を10時に固定する
        summary = data_accessor.spot_to_spot_summary_dict.get(
            (combus_route.stop_list[current_stop_index].id, ref_point["id"], "1000")
        )
        # NOTE なぜか経路が存在しないペアがある
        # 例 comstop44 -> refpoint1962
        # 原因はわかっていないが、数が少ないのでいったんcontinueでしのぐ
        if not summary:
            continue
        stop_to_refpoint_duration_m, stop_to_refpoint_walk_distance_m = summary
        total_walk_distance_m = (
            spot_to_enter_stop_walk_distance_m + stop_to_refpoint_walk_distance_m
        )
        if total_walk_distance_m > MAX_WALK_DISTANCE_M:
            continue
        total_duration_m = (
            spot_to_enter_stop_duration_m
            + combus_duration
            + stop_to_refpoint_duration_m
        )
        if total_duration_m < best_duration:
            best_duration = total_duration_m
            best_route_summary = WithCombusRouteSummary(
                spot_id=spot_id,
                enter_combus_stop_id=combus_route.stop_list[start_stop_index].id,
                exit_combus_stop_id=combus_route.stop_list[current_stop_index].id,
                ref_point_id=ref_point["id"],
                duration_m=total_duration_m,
                walk_distance_m=total_walk_distance_m,
            )
    return best_route_summary


def calculate_with_combus_route_summary_for_single_spot(
    ref_point: dict,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
    spot: dict,
    target_start_time: str,
) -> WithCombusRouteSummary:
    """
    コミュニティバスを利用した経路サマリーを返却する。
    """
    stop_id_list = [stop.id for stop in combus_route.stop_list]

    best_duration = 9999
    best_route_summary = None
    for key, (
        duration_m,
        walk_distance_m,
    ) in data_accessor.spot_to_spot_summary_dict.items():
        spot_id, stop_id, start_time_key = key
        # 関係ないspotならcontinue
        if spot_id != spot["id"]:
            continue
        # 時刻が一致していなければcontinue
        if target_start_time != start_time_key:
            continue
        # コミュニティバスに含まれないバス停ならcontinue
        if stop_id not in stop_id_list:
            continue
        stop_index = stop_id_list.index(stop_id)
        # 当該のバス停で乗る最適経路を計算
        route_summary = calculate_with_combus_route_summary_for_single_spot_and_stop(
            ref_point,
            duration_m,
            walk_distance_m,
            data_accessor,
            combus_route,
            stop_index,
            spot_id,
        )
        if route_summary is None:
            continue
        if route_summary.duration_m < best_duration:
            best_duration = route_summary.duration_m
            best_route_summary = route_summary
    return best_route_summary


def calculate_with_combus_route_summary(
    ref_point: dict,
    spot_list: dict,
    data_accessor: DataAccessor,
    combus_route: CombusRoute,
    target_max_walking_distance_m: int,
    start_time: str,
) -> WithCombusRouteSummary:
    """
    コミュニティバスを利用した経路サマリーを返却する。
    複数のスポットについて経路を得て、最も所要時間が短い経路を返却する。
    """
    best_duration = 9999
    best_route_summary = None
    for spot in spot_list:
        route_summary = calculate_with_combus_route_summary_for_single_spot(
            ref_point, data_accessor, combus_route, spot, start_time
        )
        if route_summary is None:
            continue
        if target_max_walking_distance_m < route_summary.walk_distance_m:
            continue
        if route_summary.duration_m < best_duration:
            best_duration = route_summary.duration_m
            best_route_summary = route_summary
    return best_route_summary


def convert_route_summry_to_route(
    with_combus_route_summary: WithCombusRouteSummary,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
    start_time: str,
) -> Route:
    # スポット -> 乗りバス停の経路を取得
    spot_to_enter_stop_route_dict = data_accessor.load_route(
        with_combus_route_summary.spot_id,
        with_combus_route_summary.enter_combus_stop_id,
        start_time,
    )
    spot_to_enter_stop_route = convert_to_route(spot_to_enter_stop_route_dict)

    # 降りバス停 -> 目的地の経路を取得
    # NOTE
    # コミュニティバスのバス停から目的地への経路
    # を取得する際は出発時刻を10:00に固定する
    exit_stop_to_refpoint_route_dict = data_accessor.load_route(
        with_combus_route_summary.exit_combus_stop_id,
        with_combus_route_summary.ref_point_id,
        "1000",
    )
    stop_to_refpoint_route = convert_to_route(exit_stop_to_refpoint_route_dict)

    # コミュニティバスの区間情報を取得
    def calc_next_stop_index(current_index: int, stop_list_size: int):
        if current_index == stop_list_size - 1:
            return 0
        return current_index + 1

    enter_combus_stop = data_accessor.combus_stop_dict[
        with_combus_route_summary.enter_combus_stop_id
    ]
    exit_combus_stop = data_accessor.combus_stop_dict[
        with_combus_route_summary.exit_combus_stop_id
    ]
    combus_geometry = ""
    duration_m = 0
    distance_m = 0
    enter_stop_found = False
    current_section_index = 0
    while True:
        current_section = combus_route.section_list[current_section_index]
        # セクションの入りのバス停を取得
        current_section_begin_stop_index = current_section_index
        current_section_begin_stop = combus_route.stop_list[
            current_section_begin_stop_index
        ]
        # セクションの出のバス停を取得
        current_section_end_stop_index = calc_next_stop_index(
            current_section_index, len(combus_route.stop_list)
        )
        current_section_end_stop = combus_route.stop_list[
            current_section_end_stop_index
        ]
        # 乗りのバス停から降りのバス停まで、経路形状と所要時間を足し続ける
        if (
            current_section_begin_stop.id
            == with_combus_route_summary.enter_combus_stop_id
        ):
            enter_stop_found = True
        if enter_stop_found:
            combus_geometry = merge_geometry(combus_geometry, current_section.geometry)
            duration_m += current_section.duration_m
            distance_m += int(current_section.distance_km * 1000)
            if (
                current_section_end_stop.id
                == with_combus_route_summary.exit_combus_stop_id
            ):
                break
        current_section_index = calc_next_stop_index(
            current_index=current_section_index,
            stop_list_size=len(combus_route.stop_list),
        )

    combus_route_section = RouteSection(
        mode="combus",
        from_point=RoutePoint(
            name=enter_combus_stop["name"],
            coord=Coord(lat=enter_combus_stop["lat"], lon=enter_combus_stop["lon"]),
        ),
        to_point=RoutePoint(
            name=exit_combus_stop["name"],
            coord=Coord(lat=exit_combus_stop["lat"], lon=exit_combus_stop["lon"]),
        ),
        duration_m=duration_m,
        distance_m=distance_m,
        geometry=combus_geometry,
    )

    # 三つの区間をマージする
    total_duration_m = (
        spot_to_enter_stop_route.duration_m
        + combus_route_section.duration_m
        + stop_to_refpoint_route.duration_m
    )
    total_distance_m = (
        spot_to_enter_stop_route.distance_m
        + combus_route_section.distance_m
        + stop_to_refpoint_route.distance_m
    )
    total_geometry = merge_geometry(
        merge_geometry(
            spot_to_enter_stop_route.geometry, combus_route_section.geometry
        ),
        stop_to_refpoint_route.geometry,
    )
    total_section = (
        spot_to_enter_stop_route.sections
        + [combus_route_section]
        + stop_to_refpoint_route.sections
    )
    total_walk_distance_m = (
        spot_to_enter_stop_route.walk_distance_m
        + stop_to_refpoint_route.walk_distance_m
    )

    return Route(
        from_point=spot_to_enter_stop_route.from_point,
        to_point=stop_to_refpoint_route.to_point,
        duration_m=total_duration_m,
        walk_distance_m=total_walk_distance_m,
        geometry=total_geometry,
        sections=total_section,
        distance_m=total_distance_m,
    )


def _select_spread_route_pairs(
    route_pair_list: list[tuple[Route, WithCombusRouteSummary]], k: int = 3
) -> list[tuple[Route, WithCombusRouteSummary]]:
    """ハバースイン距離に基づく最遠点優先でk件選ぶ。"""
    if len(route_pair_list) <= k:
        return route_pair_list

    def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    coords = [
        (rp[0].to_point.coord.lat, rp[0].to_point.coord.lon) for rp in route_pair_list
    ]

    avg_dists = []
    for i, (lat_i, lon_i) in enumerate(coords):
        total = 0.0
        for j, (lat_j, lon_j) in enumerate(coords):
            if i == j:
                continue
            total += haversine_m(lat_i, lon_i, lat_j, lon_j)
        avg = total / max(1, len(coords) - 1)
        avg_dists.append((avg, i))
    _, first_idx = max(avg_dists, key=lambda x: x[0])

    selected_indices = [first_idx]
    remaining_indices = [i for i in range(len(coords)) if i != first_idx]

    while len(selected_indices) < k and remaining_indices:
        best_idx = None
        best_min_dist = -1.0
        for idx in remaining_indices:
            lat_i, lon_i = coords[idx]
            min_dist = min(
                haversine_m(lat_i, lon_i, coords[s][0], coords[s][1])
                for s in selected_indices
            )
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_idx = idx
        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)

    return [route_pair_list[i] for i in selected_indices]


def calculate_route_pairs(
    data_accessor: DataAccessor,
    diff_polygon: MultiPolygon,
    spot_list: dict,
    target_max_limit: int,
    target_max_walking_distance_m: int,
    combus_route: CombusRoute,
    start_time: str,
) -> list[RoutePair]:
    """RoutePairリストを返却する。"""
    ref_point_list = data_accessor.ref_point_list["ref-points"]
    ref_point_in_polygon = filter_ref_points_in_diff_polygon(
        ref_point_list, diff_polygon
    )

    route_pair_list = []
    for ref_point in ref_point_in_polygon:
        original_route: Route = calculate_original_route(
            ref_point, spot_list, data_accessor, start_time
        )
        with_combus_route_summary: WithCombusRouteSummary = (
            calculate_with_combus_route_summary(
                ref_point,
                spot_list,
                data_accessor,
                combus_route,
                target_max_walking_distance_m,
                start_time,
            )
        )
        if original_route is None or with_combus_route_summary is None:
            continue

        # originalが無効、かつwith_combusが有効なものを抽出
        original_route_is_invalid = (
            original_route.duration_m > target_max_limit
            or original_route.walk_distance_m > target_max_walking_distance_m
        )
        if not original_route_is_invalid:
            continue
        with_combus_route_is_valid = (
            with_combus_route_summary.duration_m <= target_max_limit
            and with_combus_route_summary.walk_distance_m
            <= target_max_walking_distance_m
        )
        if not with_combus_route_is_valid:
            continue
        route_pair_list.append((original_route, with_combus_route_summary))

    selected_route_summary_list = _select_spread_route_pairs(route_pair_list, 3)
    return [
        RoutePair(
            original=original_route,
            with_combus=convert_route_summry_to_route(
                with_combus_route_summary, combus_route, data_accessor, start_time
            ),
        )
        for original_route, with_combus_route_summary in selected_route_summary_list
    ]


def modify_org_dst_names(org_route_pairs: list[RoutePair], spot_name: str) -> None:
    for route_pair in org_route_pairs:
        # original
        original_route = route_pair.original
        original_route.from_point.name = spot_name
        original_route.to_point.name = "目的地"
        original_route.sections[0].from_point.name = spot_name
        original_route.sections[-1].to_point.name = "目的地"
        # with_combus
        with_combus_route = route_pair.with_combus
        with_combus_route.from_point.name = spot_name
        with_combus_route.to_point.name = "目的地"
        with_combus_route.sections[0].from_point.name = spot_name
        with_combus_route.sections[0].to_point.name = with_combus_route.sections[
            1
        ].from_point.name
        with_combus_route.sections[-1].to_point.name = "目的地"
        with_combus_route.sections[-1].from_point.name = with_combus_route.sections[
            -2
        ].to_point.name


def exec_single_spot_type(
    spot_type: SpotType,
    spot_list: dict,
    target_max_limit: int,
    target_max_walking_distance_m: int,
    spot_to_spot_summary_dict: dict,
    combus_route: CombusRoute,
    data_accessor: DataAccessor,
    start_time: str,
) -> AreaSearchResult:
    """
    指定されたスポットタイプに対してエリア検索を実行する。
    """
    score_max = sum(mesh["population"] for mesh in data_accessor.mesh_dict.values())
    original_reachable_geojson = calc_original_reachable_geojson(
        spot_list,
        target_max_limit,
        target_max_walking_distance_m,
        data_accessor,
        start_time,
    )
    original_score = calc_score(
        data_accessor, original_reachable_geojson.reachable_mesh_codes
    )
    original_score_rate = int(original_score * 100 / score_max)
    with_combus_reachable_geojson = calc_with_combus_reachable_geojson(
        spot_list,
        target_max_limit,
        target_max_walking_distance_m,
        spot_to_spot_summary_dict,
        combus_route,
        data_accessor,
        start_time,
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
        data_accessor,
        diff_polygon,
        spot_list,
        target_max_limit,
        target_max_walking_distance_m,
        combus_route,
        start_time,
    )

    modify_org_dst_names(route_pairs, spot_list[0]["name"])

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
    spot_to_spot_summary_dict = data_accessor.spot_to_spot_summary_dict

    combus_route = create_combus_route(
        search_input.combus_stops, combus_stop_dict, combus_route_dict
    )

    # spot_id -> SpotType の辞書を作成
    spot_type_mapping = {
        "hospital": SpotType.HOSPITAL,
        "shopping": SpotType.SHOPPING,
        "public-facility": SpotType.PUBLIC_FACILITY,
    }
    spot_type_dict = {}
    spot_dict = {}
    for spot_type, spot_list_ in all_spot_list.items():
        for spot in spot_list_:
            spot_type_dict[spot["id"]] = spot_type_mapping[spot_type]
            spot_dict[spot["id"]] = spot

    # target_spotが指定されている場合はそっちを優先
    if search_input.target_spot != "":
        spot_list = [spot_dict[search_input.target_spot]]
        if search_input.target_spot not in spot_type_dict:
            raise Exception(
                f"指定されたスポットIDが存在しません。{search_input.target_spot}"
            )
        spot_type = spot_type_dict[search_input.target_spot]
    else:
        spot_list = all_spot_list[search_input.target_spot_type.value]
        spot_type = search_input.target_spot_type

    area_search_result: AreaSearchResult = exec_single_spot_type(
        spot_type,
        spot_list,
        search_input.max_minute,
        search_input.max_walking_distance_m,
        spot_to_spot_summary_dict,
        combus_route,
        data_accessor,
        search_input.start_time,
    )

    if search_input.visualize:
        output_visualize_data(area_search_result, spot_type, combus_route)

    return AreaSearchOutput(
        area_search_result=area_search_result, combus_route=combus_route
    )


def exec_area_search_all(data_accessor: DataAccessor) -> AllAreaSearchOutput:
    """
    すべての上限時間・スポットタイプで到達圏探索を実行する。
    """
    time_limit_list = [time_m for time_m in range(30, 100, 10)]
    time_limit_list = [30, 40, 50, 60]
    walk_distance_limit_list = [500, 1000]
    start_time_list = ["10:00", "13:00", "15:25"]
    result_list: list[AllAreaSearchResult] = []

    for spot_list in data_accessor.spot_list.values():
        for spot in spot_list:
            for time_limit in time_limit_list:
                for walk_distance_limit in walk_distance_limit_list:
                    for start_time in start_time_list:
                        spot_list = [spot]
                        reachable_geojson = calc_original_reachable_geojson(
                            spot_list,
                            time_limit,
                            walk_distance_limit,
                            data_accessor,
                            start_time.replace(":", ""),
                        )
                        score = calc_score(
                            data_accessor, reachable_geojson.reachable_mesh_codes
                        )
                        result_list.append(
                            AllAreaSearchResult(
                                spot=spot,
                                time_limit=time_limit,
                                walk_distance_limit=walk_distance_limit,
                                polygon=reachable_geojson.polygon,
                                score=score,
                                start_time=start_time,
                            )
                        )

    return AllAreaSearchOutput(result_list=result_list)
