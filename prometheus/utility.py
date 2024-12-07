import random
import string
import time
import pickle
from pathlib import Path
from response import CarResponse


def generate_random_string(length=12):
    """指定された長さのランダム文字列を生成する。"""
    random.seed(time.time())
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def save_to_binary_file(obj: CarResponse):
    """オブジェクトをバイナリ形式で保存する。"""
    path = f"./routes/{obj.route_id}"
    with open(path, "wb") as file:
        pickle.dump(obj.model_dump(), file)


def load_from_binary_file(route_id: str):
    """指定されたroute_idのルートをキャッシュから読み取って返却する。"""
    file_path = f"./routes/{route_id}"
    if not Path(file_path).is_file():
        raise FileNotFoundError(f"{route_id}のルートキャッシュが存在しません。")
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return CarResponse(**data)
