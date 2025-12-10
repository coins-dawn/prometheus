import json
import os
import simplekml
import polyline
from prometheus.area.area_search_output import AreaSearchResult, CombusRoute
from prometheus.area.spot_type import SpotType
from shapely.geometry import MultiPolygon, Polygon, mapping


def _create_polygon_feature(polygon, feature_type: str, spot_type: str):
    """ポリゴンのGeoJSON Featureを作成"""
    return {
        "type": "Feature",
        "geometry": mapping(polygon),
        "properties": {"type": feature_type, "spot_type": spot_type},
    }


def _create_spot_feature(spot, spot_type: str):
    """スポットのGeoJSON Featureを作成"""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [spot.coord.lon, spot.coord.lat],
        },
        "properties": {"name": spot.name, "spot_type": spot_type},
    }


def _save_polygon_geojson(
    polygons: MultiPolygon,
    spots: list,
    feature_type: str,
    spot_type: str,
    output_path: str,
):
    """ポリゴンとスポットをGeoJSONとして保存"""
    if polygons.is_empty:
        return

    features = []
    # ポリゴンの追加
    for polygon in polygons.geoms:
        features.append(_create_polygon_feature(polygon, feature_type, spot_type))

    # スポットの追加
    for spot in spots:
        features.append(_create_spot_feature(spot, spot_type))

    geojson = {"type": "FeatureCollection", "features": features}
    with open(output_path, "w") as f:
        json.dump(geojson, f)


def _save_original_polygon(
    area_search_result: AreaSearchResult, spot_type: SpotType, base_dir: str
):
    """オリジナルの到達圏ポリゴンを保存"""
    _save_polygon_geojson(
        area_search_result.reachable.original,
        area_search_result.spots,
        "original",
        spot_type.value,
        f"{base_dir}/original_{spot_type.value}.geojson",
    )


def _save_with_combus_polygon(
    area_search_result: AreaSearchResult, spot_type: SpotType, base_dir: str
):
    """コミュニティバスありの到達圏ポリゴンを保存"""
    _save_polygon_geojson(
        area_search_result.reachable.with_combus,
        area_search_result.spots,
        "with_combus",
        spot_type.value,
        f"{base_dir}/with_combus_{spot_type.value}.geojson",
    )


def _save_combus_route_kml(combus_route: CombusRoute, base_dir: str):
    """コミュニティバスの経路とバス停をKMLで保存"""
    if not combus_route:
        return

    kml = simplekml.Kml()

    # バス停の追加
    for stop in combus_route.stop_list:
        point = kml.newpoint(name=stop.name)
        point.coords = [(stop.coord.lon, stop.coord.lat)]
        point.style.iconstyle.color = simplekml.Color.red
        point.style.iconstyle.scale = 1.0

    # バス路線の追加
    for section in combus_route.section_list:
        coords = polyline.decode(section.geometry)
        line = kml.newlinestring(
            name=f"バス路線（所要時間: {section.duration_m}分, 距離: {section.distance_km:.1f}km）"
        )
        line.coords = [(lon, lat) for lat, lon in coords]
        line.style.linestyle.color = simplekml.Color.blue
        line.style.linestyle.width = 4

    kml.save(f"{base_dir}/combus_route.kml")


def _save_route_pairs_kml(area_search_result: AreaSearchResult, base_dir: str):
    """area_search_result.route_pairs を KML に出力（各ペアごとに別ファイル）"""
    route_pairs = getattr(area_search_result, "route_pairs", None)
    if not route_pairs:
        return

    def route_to_coords(route) -> list[tuple]:
        """Route -> list of (lon, lat) for KML. geometry があれば優先してデコード、なければ sections から作成。"""
        if not route:
            return []
        geom = getattr(route, "geometry", None)
        if geom:
            try:
                pts = polyline.decode(geom)  # list of (lat, lon)
                return [(lon, lat) for lat, lon in pts]
            except Exception:
                pass
        coords = []
        for sec in getattr(route, "sections", []) or []:
            try:
                fp = sec.from_point.coord
                tp = sec.to_point.coord
                coords.append((fp.lon, fp.lat))
                coords.append((tp.lon, tp.lat))
            except Exception:
                continue
        # 連続重複点を削除
        filtered = []
        for c in coords:
            if not filtered or (
                abs(filtered[-1][0] - c[0]) > 1e-9 or abs(filtered[-1][1] - c[1]) > 1e-9
            ):
                filtered.append(c)
        return filtered

    for idx, pair in enumerate(route_pairs):
        # original を別ファイルで出力
        orig_coords = route_to_coords(getattr(pair, "original", None))
        if orig_coords:
            kml_orig = simplekml.Kml()
            line = kml_orig.newlinestring(name=f"route_pair_{idx}_original")
            line.coords = orig_coords
            line.style.linestyle.color = simplekml.Color.green
            line.style.linestyle.width = 3
            kml_orig.save(f"{base_dir}/route_pair_{idx}_original.kml")

        # with_combus を別ファイルで出力
        wc_coords = route_to_coords(getattr(pair, "with_combus", None))
        if wc_coords:
            kml_wc = simplekml.Kml()
            line = kml_wc.newlinestring(name=f"route_pair_{idx}_with_combus")
            line.coords = wc_coords
            line.style.linestyle.color = simplekml.Color.red
            line.style.linestyle.width = 3
            kml_wc.save(f"{base_dir}/route_pair_{idx}_with_combus.kml")


def output_visualize_data(
    area_search_result: AreaSearchResult, spot_type: SpotType, combus_route: CombusRoute
):
    """可視化データを出力"""
    base_dir = "visualize/"

    if not os.path.exists(base_dir):
        return

    _save_original_polygon(area_search_result, spot_type, base_dir)
    _save_with_combus_polygon(area_search_result, spot_type, base_dir)
    _save_combus_route_kml(combus_route, base_dir)
    _save_route_pairs_kml(area_search_result, base_dir)
