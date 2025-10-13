import json
import simplekml
from prometheus.area.area_search_output import AreaSearchResult, CombusRoute
from prometheus.area.spot_type import SpotType


def output_visualize_data(
    area_search_result: AreaSearchResult, spot_type: SpotType, combus_route: CombusRoute
):
    base_dir = "visualize/"

    # originalポリゴンを保存
    if not area_search_result.reachable.original.is_empty:
        original_features = []

        # ポリゴンの追加
        for polygon in area_search_result.reachable.original.geoms:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[coord[0], coord[1]] for coord in polygon.exterior.coords]
                    ],
                },
                "properties": {"type": "original", "spot_type": spot_type.value},
            }
            original_features.append(feature)

        # スポットの追加
        for spot in area_search_result.spots:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [spot.coord.lon, spot.coord.lat],
                },
                "properties": {"name": spot.name, "spot_type": spot_type.value},
            }
            original_features.append(feature)

        geojson = {"type": "FeatureCollection", "features": original_features}

        with open(f"{base_dir}/original_{spot_type.value}.geojson", "w") as f:
            json.dump(geojson, f)

    # with_combuserポリゴンを保存
    if not area_search_result.reachable.with_comnuter.is_empty:
        with_combus_features = []

        # ポリゴンの追加
        for polygon in area_search_result.reachable.with_comnuter.geoms:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[coord[0], coord[1]] for coord in polygon.exterior.coords]
                    ],
                },
                "properties": {"type": "with_combus", "spot_type": spot_type.value},
            }
            with_combus_features.append(feature)

        # スポットの追加
        for spot in area_search_result.spots:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [spot.coord.lon, spot.coord.lat],
                },
                "properties": {"name": spot.name, "spot_type": spot_type.value},
            }
            with_combus_features.append(feature)

        geojson = {"type": "FeatureCollection", "features": with_combus_features}

        with open(f"{base_dir}/with_combus_{spot_type.value}.geojson", "w") as f:
            json.dump(geojson, f)
            
            
    # コミュニティバスの経路とバス停をkmlで保存
    if combus_route:
        kml = simplekml.Kml()

        # バス停の追加
        for stop in combus_route.stop_list:
            point = kml.newpoint(name=stop.name)
            point.coords = [(stop.coord.lon, stop.coord.lat)]
            point.style.iconstyle.color = simplekml.Color.red
            point.style.iconstyle.scale = 1.0

        # バス路線の追加
        for section in combus_route.section_list:
            # Google Polyline形式のgeometryを座標列に変換
            import polyline
            coords = polyline.decode(section.geometry)  # [(lat, lon), ...]
            
            line = kml.newlinestring(
                name=f"バス路線（所要時間: {section.duration_m}分, 距離: {section.distance_km:.1f}km）"
            )
            line.coords = [(lon, lat) for lat, lon in coords]
            line.style.linestyle.color = simplekml.Color.blue
            line.style.linestyle.width = 4  # 線の太さを4に設定

        kml.save(f"{base_dir}/combus_route.kml")