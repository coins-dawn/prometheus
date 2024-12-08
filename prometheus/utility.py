import random
import string
import time
import pickle
import polyline
import math
from pathlib import Path
from response import CarResponse
from xml.etree.ElementTree import Element, SubElement, tostring


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
    for subroute in car_response.subroutes:
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
    for subroute in car_response.subroutes:
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
