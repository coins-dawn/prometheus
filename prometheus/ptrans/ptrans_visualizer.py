import simplekml
import polyline
from prometheus.ptrans.ptrans_output import PtransOutputRoute


def generate_ptrans_route_kml(
    ptrans_route: PtransOutputRoute, output_path="ptrans_result.kml"
):
    kml = simplekml.Kml()

    # スポット（ピン）の作成
    for spot in ptrans_route.spots:
        kml.newpoint(
            name=spot.name, coords=[(spot.coord.lon, spot.coord.lat)]  # (lon, lat)
        )

    # セクション（線）の作成
    for i, section in enumerate(ptrans_route.sections):
        if section.shape:
            coords = polyline.decode(section.shape)  # [(lat, lon), ...]
            line = kml.newlinestring(coords=[(lon, lat) for lat, lon in coords])
            # 色分けしたい場合はここで section.type で色を変えることも可能
            line.style.linestyle.color = simplekml.Color.blue
            line.style.linestyle.width = 5.0  # 線の太さを指定
        else:
            org_spot = ptrans_route.spots[i]
            dst_spot = ptrans_route.spots[i + 1]
            # org_spotからdst_spotまでを赤の直線でlineに追加
            coords = [
                (org_spot.coord.lon, org_spot.coord.lat),
                (dst_spot.coord.lon, dst_spot.coord.lat),
            ]
            line = kml.newlinestring(coords=coords)
            line.style.linestyle.color = simplekml.Color.lightpink
            line.style.linestyle.width = 5.0

    kml.save(output_path)
