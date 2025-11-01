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
