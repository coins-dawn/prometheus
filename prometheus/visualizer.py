import simplekml


def export_kml(nodes_df, route_nodes, node_sequence, output_file="route.kml"):
    kml = simplekml.Kml()

    # 経路のライン
    line_coords = []
    for node_id in route_nodes:
        node = nodes_df[nodes_df["ノード番号"] == node_id]
        if node.empty:
            continue
        lat = node["緯度"].values[0]
        lon = node["経度"].values[0]
        line_coords.append((lon, lat))

    # 赤の太いライン
    linestring = kml.newlinestring(name="経路")
    linestring.coords = line_coords
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 5  # 太さ

    # ピンの追加（訪問ノードのみ）
    for idx, node_id in enumerate(node_sequence):
        node = nodes_df[nodes_df["ノード番号"] == node_id]
        if node.empty:
            continue
        lat = node["緯度"].values[0]
        lon = node["経度"].values[0]
        pnt = kml.newpoint(name=f"目的地 {idx+1}", coords=[(lon, lat)])
        pnt.style.labelstyle.scale = 1.2
        pnt.style.iconstyle.icon.href = (
            "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
        )

    # ファイル保存
    kml.save(output_file)
    print(f">>> KMLファイルを出力しました: {output_file}")
