from math import floor
import math
from prometheus.coord import Coord


def latlon_to_mesh(coord: Coord) -> int:
    """3次メッシュコードを計算する。"""
    lat, lon = coord.lat, coord.lon
    primary = floor(lat * 1.5) * 100 + floor(lon - 100)
    secondary = floor((lat * 60) % 40 / 5) * 10 + floor((lon * 60) % 60 / 7.5)
    tertiary = floor((lat * 3600) % 300 / 30) * 10 + floor((lon * 3600) % 450 / 45)

    return int(f"{primary}{secondary}{tertiary}")


def haversine(coord1: Coord, coord2: Coord) -> int:
    """2点の距離を計算する。"""
    lat1, lon1 = coord1.lat, coord1.lon
    lat2, lon2 = coord2.lat, coord2.lon
    R = 6371000  # 地球の半径 (メートル)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
