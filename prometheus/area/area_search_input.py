from prometheus.area.spot_type import SpotType


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

        # combus
        self.combus = None
