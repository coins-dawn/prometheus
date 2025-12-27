from prometheus.area.spot_type import SpotType


WALKING_DISTANCE_DEFAULT_M = 1000  # 徒歩距離の上限[m]


class AreaSearchInput:
    def __init__(self, data: dict):
        spots_mapping = {
            "hospital": SpotType.HOSPITAL,
            "shopping": SpotType.SHOPPING,
            "public-facility": SpotType.PUBLIC_FACILITY,
        }

        # target_spot_type or target_spot のいずれかは必須
        if "target-spot-type" not in data and "target-spot" not in data:
            raise Exception(
                "target-spot-type か target-spot のいずれかを指定してください。"
            )

        # target_spot_type
        self.target_spot_type: SpotType = None
        if "target-spot-type" in data:
            target_spot = data["target-spot-type"]
            if target_spot not in spots_mapping:
                raise Exception(f"不明なスポットタイプです: {target_spot}")
            self.target_spot_type = spots_mapping[target_spot]

        # target_spot
        self.target_spot = ""
        if "target-spot" in data:
            self.target_spot = data["target-spot"]

        # max_minute
        if "max-minute" not in data:
            raise Exception("max-minute が存在しません。")
        max_minute_str = data["max-minute"]
        if (
            not isinstance(max_minute_str, int)
            or max_minute_str <= 0
            or max_minute_str > 120
        ):
            raise Exception("max-minute は0から120の間の正の整数で指定してください。")
        self.max_minute = int(max_minute_str)

        # max_walking_distance
        self.max_walking_distance_m = WALKING_DISTANCE_DEFAULT_M
        if "max-walk-distance" not in data:
            raise Exception("max-walk-distanceが存在しません。")
        max_walking_distance_str = data["max-walk-distance"]
        if not isinstance(max_walking_distance_str, int):
            raise Exception("max-walk-distance は整数で指定してください。")
        max_walking_distance_m = int(max_walking_distance_str)
        if (
            max_walking_distance_m < 0
            or max_walking_distance_m > WALKING_DISTANCE_DEFAULT_M
        ):
            raise Exception("max-walk-distance は0から1000の間で指定してください。")
        self.max_walking_distance_m = max_walking_distance_m

        # combus_stops
        if "combus-stops" not in data:
            self.combus_stops = []
            return
        combus_stops = data["combus-stops"]
        if not isinstance(combus_stops, list):
            raise Exception("combus-stopsはリスト形式で指定してください")
        if not all(isinstance(stop, str) for stop in combus_stops):
            raise Exception("combus-stopsの要素は全て文字列で指定してください")
        self.combus_stops = combus_stops
