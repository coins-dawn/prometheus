import os
import zipfile
import requests

ARCHIVE_DATA_DOWNLOAD_URL = (
    "https://github.com/coins-dawn/soaring/releases/download/v3.0.0/archive.zip"
)
ARCHIVE_FILE_PATH = "data/archive.zip"
EXPAND_TARGET_DIR = "data/archive/"


def download_archive():
    print("データのダウンロードを開始します...")
    os.makedirs(os.path.dirname(ARCHIVE_FILE_PATH), exist_ok=True)
    with requests.get(
        ARCHIVE_DATA_DOWNLOAD_URL, timeout=30, allow_redirects=True, stream=True
    ) as resp:
        resp.raise_for_status()
        with open(ARCHIVE_FILE_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print("データのダウンロードが完了しました。")


def arrange_data():
    if os.path.exists(EXPAND_TARGET_DIR):
        print("データはすでに展開されています。")
        return

    if not os.path.exists(ARCHIVE_FILE_PATH):
        download_archive()

    print("zipファイルの展開を開始します...")
    with zipfile.ZipFile(ARCHIVE_FILE_PATH, "r") as zip_ref:
        zip_ref.extractall(EXPAND_TARGET_DIR)
    print("zipファイルの展開が完了しました。")
