import pandas as pd
import networkx as nx
import simplekml
import math
from math import floor

def latlon_to_mesh(lat, lon):
    """3次メッシュコードを計算"""
    primary = floor(lat * 1.5) * 100 + floor(lon - 100)
    secondary = floor((lat * 60) % 40 / 5) * 10 + floor((lon * 60) % 60 / 7.5)
    tertiary = floor((lat * 3600) % 300 / 30) * 10 + floor((lon * 3600) % 450 / 45)

    return int(f"{primary}{secondary}{tertiary}")

def create_mesh_dict(nodes_df):
    mesh_dict = {}
    for _, row in nodes_df.iterrows():
        mesh_id = row['3次メッシュID']
        if mesh_id not in mesh_dict:
            mesh_dict[mesh_id] = []
        mesh_dict[mesh_id].append(row['ノード番号'])
    return mesh_dict

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球の半径 (メートル)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def find_nearest_node(lat, lon, nodes_df, mesh_dict):
    mesh_id = latlon_to_mesh(lat, lon)
    candidates = nodes_df[nodes_df['ノード番号'].isin(mesh_dict.get(mesh_id, []))]
    
    if candidates.empty:
        candidates = nodes_df  # メッシュ内にない場合は全体から探す
    
    return candidates.loc[candidates.apply(lambda row: haversine(lat, lon, row['緯度'], row['経度']), axis=1).idxmin(), 'ノード番号']

def load_graph(nodes_file, ways_file):
    nodes_df = pd.read_csv(nodes_file)
    ways_df = pd.read_csv(ways_file)
    
    G = nx.DiGraph()
    for _, row in ways_df.iterrows():
        G.add_edge(row['出発地のノード番号'], row['到着側のノード番号'], weight=row['ウェイの距離[m]'])
    
    return G, nodes_df

def find_shortest_path(graph, start_node, end_node):
    return nx.shortest_path(graph, source=start_node, target=end_node, weight='weight'), nx.shortest_path_length(graph, source=start_node, target=end_node, weight='weight')

def generate_kml(nodes_df, path, output_file='route.kml'):
    kml = simplekml.Kml()
    
    for node in path:
        row = nodes_df[nodes_df['ノード番号'] == node].iloc[0]
        kml.newpoint(name=str(node), coords=[(row['経度'], row['緯度'])])
    
    linestring = kml.newlinestring(name='Shortest Path',
                                   coords=[(nodes_df[nodes_df['ノード番号'] == n].iloc[0]['経度'], 
                                            nodes_df[nodes_df['ノード番号'] == n].iloc[0]['緯度']) for n in path])
    linestring.style.linestyle.color = simplekml.Color.red
    linestring.style.linestyle.width = 5
    
    kml.save(output_file)
