import json
import pickle


def convert_time(start_time: str) -> str:
    """時刻の形式を変換（例: 10:00am -> 1000, 3:25pm -> 1525）"""
    is_pm = start_time.endswith("pm")
    time_part = start_time[:-2]  # "am"または"pm"を削除
    # 時間と分を分割
    hours_str, minutes = time_part.split(":")
    hours = int(hours_str)
    # pmの場合は時間に12を足す（ただし12pmは12時のまま）
    if is_pm and hours != 12:
        hours += 12
    elif not is_pm and hours == 12:  # 12amは00時
        hours = 0
    return f"{hours:02d}{minutes}"


class DataAccessor:
    SPOT_LIST_FILE_PATH = "data/archive/spot_list.json"
    COMBUS_STOP_LIST_FILE_PATH = "data/archive/combus_stops.json"
    REF_POINTS_LIST_FILE_PATH = "data/archive/ref_points.json"
    COMBUS_ROUTES_FILE_PATH = "data/archive/combus_routes.json"
    ALL_ROUTES_FILE_PATH = "data/archive/all_routes.csv"
    ALL_GEOJSON_FILE_PATH = "data/archive/all_geojsons.txt"
    MESH_FILE_PATH = "data/archive/mesh.json"
    BEST_COMBUS_STOP_SEQUENCE_FILE_PATH = "data/static/best_combus_stop_sequences.json"
    TARGET_REGION_FILE_PATH = "data/archive/target_region.json"
    STATIC_RESPONSE_FILE_PATH = "data/static/request_response.bin"
    PTRANS_FILE_PATH = "data/archive/ptrans.json"

    def __init__(self):
        self.spot_list = DataAccessor.load_spot_list()
        self.combus_stop_list = DataAccessor.load_combus_stop_list()
        self.combus_stop_dict = DataAccessor.load_combus_stop_dict()
        self.ref_point_list = DataAccessor.load_ref_point_list()
        self.combus_route_dict = DataAccessor.load_combus_route_dict()
        self.spot_to_spot_summary_dict = DataAccessor.load_spot_to_spot_summary_dict()
        self.geojson_name_key_dict = DataAccessor.load_geojson_name_key_dict()
        self.mesh_dict = DataAccessor.load_mesh_dict()
        self.best_combus_stop_sequence_dict = (
            DataAccessor.load_best_combus_stop_sequences()
        )
        self.target_region_dict = DataAccessor.load_target_region()
        self.static_request_response_dict = DataAccessor.load_static_request_response()
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
    def load_ref_point_list(cls):
        """
        参照地点一覧をロードしlist型式で返却する。
        """
        with open(cls.REF_POINTS_LIST_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

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
    def load_geojson_name_key_dict(cls):
        """
        geojsonファイル名のキー辞書をロードしdictで返却する。
        id_strをキーに、(max_minute, max_distance)のリストを値とする。
        リストはmax_minute、次にmax_distanceの降順でソートされる。
        """
        all_geojson_name_key_dict = {}
        with open(cls.ALL_GEOJSON_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                file_name = line.strip()
                # .bin拡張子を削除
                if file_name.endswith(".bin"):
                    file_name = file_name[:-4]
                # _で分割
                parts = file_name.split("_")
                assert len(parts) == 4
                id_str = parts[0]
                max_minute = int(parts[1])
                max_distance = int(parts[2])
                start_time = parts[3]
                if (id_str, start_time) not in all_geojson_name_key_dict:
                    all_geojson_name_key_dict[(id_str, start_time)] = []
                all_geojson_name_key_dict[(id_str, start_time)].append(
                    (max_minute, max_distance)
                )
        # 各キーのリストをmax_minute、次にmax_distanceで降順ソート
        for key in all_geojson_name_key_dict:
            all_geojson_name_key_dict[key].sort(
                key=lambda x: (x[0], x[1]), reverse=True
            )
        return all_geojson_name_key_dict

    @classmethod
    def load_spot_to_spot_summary_dict(cls):
        """
        スポット間のサマリー辞書をロードしdictで返却する。
        """
        spot_to_spot_summary_dict = {}
        with open(cls.ALL_ROUTES_FILE_PATH, "r", encoding="utf-8") as f:
            next(f)  # ヘッダー行をスキップ
            for line in f:
                parts = line.strip().split(",")
                from_spot = parts[0]
                to_spot = parts[1]
                start_time = convert_time(parts[2])
                duration_m = int(parts[3])
                walk_distance_m = int(parts[4])
                spot_to_spot_summary_dict[(from_spot, to_spot, start_time)] = (
                    duration_m,
                    walk_distance_m,
                )
        return spot_to_spot_summary_dict

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
                "geometry": mesh["geometry"],
            }
            for mesh in mesh_list
        }
        return mesh_dict

    @classmethod
    def load_best_combus_stop_sequences(cls):
        """最適なバス停列を辞書形式で返却する。"""
        with open(cls.BEST_COMBUS_STOP_SEQUENCE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load_target_region(cls):
        """ターゲットリージョンを辞書型式で返却する。"""
        with open(cls.TARGET_REGION_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_geojson(
        self, id_str: str, max_minute: int, max_walking_distance_m: int, start_time: str
    ):
        """
        指定されたID、最大時間、徒歩距離上限に対応するgeojsonをロードする。
        """
        minute_walk_distance_list = self.geojson_name_key_dict[(id_str, start_time)]
        for geojson_minute, geojson_walk_distance in minute_walk_distance_list:
            if geojson_minute > max_minute:
                continue
            if geojson_walk_distance > max_walking_distance_m:
                continue
            file_name = (
                f"{id_str}_{geojson_minute}_{geojson_walk_distance}_{start_time}.bin"
            )
            file_path = f"data/archive/geojson/{file_name}"
            with open(file_path, "rb") as f:
                return pickle.load(f)
        return None

    def load_route(self, from_id: str, to_id: str, start_time: str):
        """
        指定されたfrom_idとto_idに対応する経路情報を返却する。
        pickle形式（.bin）で保存されたファイルを読み込む。
        """
        file_path = f"data/archive/route/{from_id}_{to_id}_{start_time}.bin"
        with open(file_path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def load_static_request_response(cls):
        """
        事前に保存されたリクエストとレスポンスのペアをロードする。
        """
        static_response_list = []
        with open(cls.STATIC_RESPONSE_FILE_PATH, "rb") as f:
            static_response_list = pickle.load(f)

        static_request_response_dict = {}
        for elem in static_response_list:
            request = elem["request"]
            response = elem["response"]
            key = (
                request["target-spot"],
                request["max-minute"],
                request["max-walk-distance"],
                request["start-time"],
                tuple(request["combus-stops"]),
            )
            static_request_response_dict[key] = response
        return static_request_response_dict

    @classmethod
    def load_ptrans(cls):
        """
        公共交通機関のデータをロードする。
        """
        with open(cls.PTRANS_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
