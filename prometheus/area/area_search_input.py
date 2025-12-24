from prometheus.area.spot_type import SpotType


WALKING_DISTANCE_DEFAULT_M = 1000  # 徒歩距離の上限[m]


class AreaSearchInput:
    def __init__(self, data: dict):
        spots_mapping = {
            "hospital": SpotType.HOSPITAL,
            "shopping": SpotType.SHOPPING,
            "public-facility": SpotType.PUBLIC_FACILITY,
        }

        # target spots
        self.target_spots: list[SpotType] = []
        target_spots = data.get("target-spots", [])
        if not target_spots:
            raise Exception("target-spots が存在しません。")
        for target_spot in target_spots:
            if target_spot not in spots_mapping:
                raise Exception(f"不明なスポットタイプです: {target_spot}")
            self.target_spots.append(spots_mapping[target_spot])

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
            self.max_walking_distance_m = WALKING_DISTANCE_DEFAULT_M
        else:
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
