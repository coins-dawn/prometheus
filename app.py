import networkx as nx
from flask import Flask, request, jsonify
from search import find_nearest_node, find_shortest_path, generate_kml, load_graph, create_mesh_dict

app = Flask(__name__)

# ネットワークのロード
base_path = "convert/output"
print(">>>> ネットワークをロードしています。")
G, nodes_df = load_graph(f'{base_path}/car_nodes.csv', f'{base_path}/car_ways.csv')
mesh_dict = create_mesh_dict(nodes_df)
print("<<<< ネットワークのロードが完了しました。")

@app.route('/shortest_paths', methods=['POST'])
def shortest_paths():
    try:
        data = request.get_json()
        requests = data.get("requests", [])
        
        if not requests:
            return jsonify({"error": "No requests provided"}), 400
        
        results = []
        for i, req in enumerate(requests):
            start_lat = float(req["start_lat"])
            start_lon = float(req["start_lon"])
            end_lat = float(req["end_lat"])
            end_lon = float(req["end_lon"])

            print(f">>>> {i+1} 件目の地点登録を実行しています。")    
            start_node = find_nearest_node(start_lat, start_lon, nodes_df, mesh_dict)
            end_node = find_nearest_node(end_lat, end_lon, nodes_df, mesh_dict)
            print("<<<< 地点登録が完了しました。")
            
            print(f">>>> {i+1} 件目の経路探索を実行しています。")
            path, length = find_shortest_path(G, start_node, end_node)
            print("<<<< 経路探索が完了しました。")
            print(f"経路長: {length} m")
            
            # if i == 0:
            #     generate_kml(nodes_df, path)
            #     print("route.kml を出力しました。")
            
            results.append({"route_length": length})
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)