import os
import zipfile

GEOJSON_ZIP_FILE_PATH = "data/area/geojson.zip"
GEOJSON_DST_DIR_PATH = "data/area/"


def unzip_geojson():
    if os.path.exists(GEOJSON_DST_DIR_PATH + "/geojson"):
        return
    print("geojsonの展開を開始します...")
    with zipfile.ZipFile(GEOJSON_ZIP_FILE_PATH, "r") as zip_ref:
        zip_ref.extractall(GEOJSON_DST_DIR_PATH)
    print("geojsonの展開が完了しました。")
