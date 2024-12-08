import random
import string
import time
import pickle
import polyline
from pathlib import Path
from response import CarResponse
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import time, timedelta, datetime


def generate_random_string(length=12):
    """指定された長さのランダム文字列を生成する。"""
    random.seed(datetime.now().timestamp())
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


def save_car_route_as_kml(car_response: CarResponse):
    """車ルートをkmlに変換して保存する。"""
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")
    style = SubElement(document, "Style", id="brightGreenLine")
    linestyle = SubElement(style, "LineStyle")
    color = SubElement(linestyle, "color")
    color.text = "ff00ff00"
    width = SubElement(linestyle, "width")
    width.text = "4"
    for subroute in car_response.route_info.subroutes:
        placemark = SubElement(document, "Placemark")
        styleurl = SubElement(placemark, "styleUrl")
        styleurl.text = "#brightGreenLine"
        name = SubElement(placemark, "name")
        name.text = f"{subroute.org.name} to {subroute.dst.name}"
        description = SubElement(placemark, "description")
        description.text = (
            f"Duration: {subroute.duration} seconds\n"
            f"Distance: {subroute.distance} meters"
        )
        line_string = SubElement(placemark, "LineString")
        coordinates = SubElement(line_string, "coordinates")
        decoded_polyline = polyline.decode(subroute.polyline)
        coordinates.text = " ".join(f"{lon},{lat},0" for lat, lon in decoded_polyline)
    for subroute in car_response.route_info.subroutes:
        stop = subroute.org
        placemark = SubElement(document, "Placemark")
        name = SubElement(placemark, "name")
        name.text = stop.name
        point = SubElement(placemark, "Point")
        coordinates = SubElement(point, "coordinates")
        coordinates.text = f"{stop.coord.lon},{stop.coord.lat},0"
    kml_data = tostring(kml, encoding="utf-8", xml_declaration=True).decode("utf-8")
    with open("car_route.kml", "w", encoding="utf-8") as file:
        file.write(kml_data)


def add_times(time1: time, time2: time) -> str:
    """timeオブジェクトの和をとり、HH:MM形式の文字列を返す。"""
    delta1 = timedelta(hours=time1.hour, minutes=time1.minute, seconds=time1.second)
    delta2 = timedelta(hours=time2.hour, minutes=time2.minute, seconds=time2.second)
    result_delta = delta1 + delta2
    total_seconds = round(result_delta.total_seconds())
    hours = int(total_seconds // 3600) % 24
    minutes = int((total_seconds % 3600) // 60)
    return f"{hours:02}:{minutes:02}"


def add_seconds_to_time(original_time: time, seconds_to_add: int) -> time:
    """timeオブジェクトに秒数を足してtimeオブジェクトを返却する。"""
    original_timedelta = timedelta(
        hours=original_time.hour,
        minutes=original_time.minute,
        seconds=original_time.second,
    )
    result_timedelta = original_timedelta + timedelta(seconds=seconds_to_add)
    total_seconds = result_timedelta.total_seconds()
    hours = int(total_seconds // 3600) % 24
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return time(hour=hours, minute=minutes, second=seconds)
