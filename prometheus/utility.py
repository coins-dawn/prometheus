import random
import string
import time
import json
import pickle
from response import CarResponse


def generate_random_string(length=12):
    """指定された長さのランダム文字列を生成する。"""
    random.seed(time.time())
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def save_to_json_file(obj: CarResponse):
    """オブジェクトをJson型式で保存する。"""
    path = f"./routes/{obj.route_id}.json"
    json_data = json.dumps(obj.model_dump(), indent=4, ensure_ascii=False)
    with open(path, "w", encoding="utf-8") as file:
        file.write(json_data)


def save_to_binary_file(obj: CarResponse):
    """オブジェクトをバイナリ形式で保存する。"""
    path = f"./routes/{obj.route_id}"
    with open(path, "wb") as file:
        pickle.dump(obj.model_dump(), file)


def load_from_binary_file(route_id: str):
    file_path = f"./routes/{route_id}"
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return CarResponse(**data)
