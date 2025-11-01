import json
import pickle


class DataAccessor:
    SPOT_LIST_FILE_PATH = "data/area/toyama_spot_list.json"
    COMBUS_STOP_LIST_FILE_PATH = "data/area/combus_stops.json"
    COMBUS_ROUTES_FILE_PATH = "data/area/combus_routes.json"
    SPOT_TO_STOPS_FILE_PATH = "data/area/spot_to_stops.json"
    ALL_GEOJSON_FILE_PATH = "data/area/all_geojsons.txt"
    MESH_FILE_PATH = "data/area/mesh.json"
    BEST_COMBUS_STOP_SEQUENCE_FILE_PATH = "data/area/best_combus_stop_sequences.json"

    def __init__(self):
        self.spot_list = DataAccessor.load_spot_list()
        self.combus_stop_list = DataAccessor.load_combus_stop_list()
        self.combus_stop_dict = DataAccessor.load_combus_stop_dict()
        self.combus_route_dict = DataAccessor.load_combus_route_dict()
        self.spot_to_stops_dict = DataAccessor.load_spot_to_stops_dict()
        self.geojson_name_set = DataAccessor.load_geojson_name_set()
        self.mesh_dict = DataAccessor.load_mesh_dict()
        self.best_combus_stop_sequence_dict = (
            DataAccessor.load_best_combus_stop_sequences()
        )
        print("データのロードが完了しました。")

    @classmethod
    def load_spot_list(cls):
        """
        スポット一覧をロードする。
        """
        with open(cls.SPOT_LIST_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load_combus_stop_list(cls):
        """
        コミュニティバスの一覧をロードする。
        """
        with open(cls.COMBUS_STOP_LIST_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load_combus_stop_dict(cls):
        """
        コミュニティバスの一覧をロードしdict型式で返却する。
        """
        combus_stop_list = cls.load_combus_stop_list()
        return {
            combus_stop["id"]: {
                "name": combus_stop["name"],
                "lat": combus_stop["lat"],
                "lon": combus_stop["lon"],
            }
            for combus_stop in combus_stop_list["combus-stops"]
        }

    @classmethod
    def load_combus_route_dict(cls):
        """
        コミュニティバスの経路一覧をロードしdict型式で返却する。
        """
        combus_route_dict = {}
        combus_route_list = []
        with open(cls.COMBUS_ROUTES_FILE_PATH, "r", encoding="utf-8") as f:
            combus_route_list = json.load(f)["combus-routes"]
        for combus_route in combus_route_list:
            from_id = combus_route["from"]
            to_id = combus_route["to"]
            combus_route_dict[(from_id, to_id)] = {
                "distance_km": float(combus_route["distance_km"]),
                "duration_m": int(combus_route["duration_m"]),
                "geometry": combus_route["geometry"],
            }
        return combus_route_dict

    @classmethod
    def load_spot_to_stops_dict(cls):
        """
        スポットからバス停までの経路情報をロードしdict型式で返却する。
        """
        spot_to_stops_list = []
        spot_to_stops_dict = {}
        with open(cls.SPOT_TO_STOPS_FILE_PATH, "r", encoding="utf-8") as f:
            spot_to_stops_list = json.load(f)["spot-to-stops"]

        for spot_to_stop in spot_to_stops_list:
            from_id = spot_to_stop["from"]
            to_id = spot_to_stop["to"]
            walk_distance_m = int(spot_to_stop["walk_distance_m"])
            spot_to_stops_dict[(from_id, to_id)] = {
                "duration_m": int(spot_to_stop["duration_m"]),
                "walk_distance_m": walk_distance_m,
            }
        return spot_to_stops_dict

    @classmethod
    def load_geojson_name_set(cls):
        """
        すべてのgeojsonの名称をロードしsetで返却する。
        """
        all_geojson_name_set = set()
        with open(cls.ALL_GEOJSON_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                all_geojson_name_set.add(name)
        return all_geojson_name_set

    @classmethod
    def load_mesh_dict(cls):
        """
        メッシュ情報をロードしdictで返却する。
        """
        mesh_list = []
        with open(cls.MESH_FILE_PATH, "r", encoding="utf-8") as f:
            mesh_list = json.load(f)["mesh"]
        mesh_dict = {
            mesh["mesh_code"]: {
                "mesh_code": mesh["mesh_code"],
                "population": mesh["population"],
                # geometryは必要に応じて追加
            }
            for mesh in mesh_list
        }
        return mesh_dict

    @classmethod
    def load_best_combus_stop_sequences(cls):
        """最適なバス停列を辞書形式で返却する。"""
        result_dict = {}
        with open(cls.BEST_COMBUS_STOP_SEQUENCE_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sequence in data["best-combus-stop-sequences"]:
                key = (sequence["spot-type"], sequence["duration-limit-m"])
                result_dict[key] = sequence["stop-sequence"]
        return result_dict

    def load_geojson(self, id_str: str, max_minute: int):
        """
        指定されたIDと最大時間に対応するgeojsonをロードする。
        対応するgeojsonファイルが存在しない場合はNoneを返す。
        """
        current_max_minute = max_minute
        while current_max_minute > 0:
            file_name = f"{id_str}_{current_max_minute}.bin"
            if file_name not in self.geojson_name_set:
                current_max_minute -= 1
                continue
            file_path = f"data/area/geojson/{file_name}"
            with open(file_path, "rb") as f:
                return pickle.load(f)
        return None
