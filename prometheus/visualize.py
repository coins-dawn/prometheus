import simplekml
import polyline
from prometheus.output import SearchOutout


def generate_kml(search_output: SearchOutout, output_path="route.kml"):
    kml = simplekml.Kml()

    # ピンの作成（Stops）
    for output_stop in search_output.route.stops:
        stop = output_stop.stop
        kml.newpoint(
            name=stop.name, coords=[(stop.coord.lon, stop.coord.lat)]  # (lon, lat)
        )

    # 線の作成（Sections）
    for section in search_output.route.sections:
        coords = polyline.decode(section.shape)  # [(lat, lon), ...]
        line = kml.newlinestring(coords=[(lon, lat) for lat, lon in coords])
        line.style.linestyle.color = simplekml.Color.lightgreen  # 緑
        line.style.linestyle.width = 4  # 太め

    # 書き出し
    kml.save(output_path)
