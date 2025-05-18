import simplekml
import polyline
from prometheus.output import CarSearchOutout


def generate_car_route_kml(search_output: CarSearchOutout, output_path="car_route.kml"):
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
        line.style.linestyle.width = 8  # 太め

    # 書き出し
    kml.save(output_path)


def generate_ptrans_route_kml(
    node_sequence: list,
    stops_dict: dict,
    shape_dict: dict,
    start_coord: tuple[float, float] = None,
    goal_coord: tuple[float, float] = None,
    output_path="ptrans_result.kml"
):
    kml = simplekml.Kml()

    # ★バス停ピン
    for idx, nodeid in enumerate(node_sequence):
        if nodeid not in stops_dict:
            continue
        lat, lon = stops_dict[nodeid]
        kml.newpoint(name=nodeid, coords=[(lon, lat)])

    # ★スタート・ゴールピン
    if start_coord:
        kml.newpoint(name="Start", coords=[(start_coord[1], start_coord[0])])
    if goal_coord:
        kml.newpoint(name="Goal", coords=[(goal_coord[1], goal_coord[0])])

    # ★スタート→最初のバス停
    if start_coord:
        first_stop_id = node_sequence[0]
        if first_stop_id in stops_dict:
            lat, lon = stops_dict[first_stop_id]
            kml.newlinestring(
                coords=[(start_coord[1], start_coord[0]), (lon, lat)]
            ).style.linestyle.color = simplekml.Color.blue

    # ★最後のバス停→ゴール
    if goal_coord:
        last_stop_id = node_sequence[-1]
        if last_stop_id in stops_dict:
            lat, lon = stops_dict[last_stop_id]
            kml.newlinestring(
                coords=[(lon, lat), (goal_coord[1], goal_coord[0])]
            ).style.linestyle.color = simplekml.Color.blue

    # ★経路線
    for i in range(len(node_sequence) - 1):
        n1 = node_sequence[i]
        n2 = node_sequence[i + 1]
        key = (n1, n2)
        if key in shape_dict:
            coords = [(c.lon, c.lat) for c in shape_dict[key]]
        else:
            # stops_dict[n1], stops_dict[n2]は(緯度, 経度)
            lat1, lon1 = stops_dict[n1]
            lat2, lon2 = stops_dict[n2]
            coords = [(lon1, lat1), (lon2, lat2)]
        line = kml.newlinestring(coords=coords)
        if str(n1).startswith("A") and str(n2).startswith("A"):
            line.style.linestyle.color = simplekml.Color.lightgreen
        else:
            line.style.linestyle.color = simplekml.Color.red
        line.style.linestyle.width = 12  # 太め

    kml.save(output_path)