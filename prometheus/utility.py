from pydantic import BaseModel
from collections import OrderedDict
import math


def convert_for_json(obj):
    if isinstance(obj, BaseModel):
        # BaseModel.dict()は順序を保持する
        return OrderedDict(obj.dict())
    elif isinstance(obj, list):
        return [convert_for_json(i) for i in obj]
    elif isinstance(obj, dict):
        # dictの順序を保持して再帰的に変換
        return OrderedDict((k, convert_for_json(v)) for k, v in obj.items())
    elif hasattr(obj, "__dataclass_fields__"):
        # dataclassも順序を保持
        return OrderedDict(
            (k, convert_for_json(getattr(obj, k))) for k in obj.__dataclass_fields__
        )
    else:
        return obj


def round_half_up(value: float) -> int:
    """floatを四捨五入して整数にする。"""
    return int(math.floor(value + 0.5))


def add_time(current_time: str, minutes: int) -> str:
    """時刻文字列（例: '10:00'）に分数を加算し、'HH:MM'形式で返す。"""
    hour, minute = map(int, current_time.split(":"))
    total_minutes = hour * 60 + minute + minutes
    new_hour = (total_minutes // 60) % 24
    new_minute = total_minutes % 60
    return f"{new_hour:02d}:{new_minute:02d}"
