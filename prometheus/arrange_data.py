import os
import sys
import zipfile
import subprocess

ARCHIVE_DATA_DOWNLOAD_URL = "https://github.com/coins-dawn/soaring/releases/download/v1.0.0/archive.zip"
ARCHIVE_FILE_PATH = "data/archive.zip"
EXPAND_TARGET_DIR = "data/archive/"

def run_curl_command():
    print("データのダウンロードを開始します...")
    COMMAND = [
        'curl',
        '-L',
        '-o',
        ARCHIVE_FILE_PATH,
        ARCHIVE_DATA_DOWNLOAD_URL
    ]
    subprocess.run(COMMAND, check=True)
    print("データのダウンロードが完了しました。")

def arrange_data():
    if os.path.exists(EXPAND_TARGET_DIR):
        print("データはすでに展開されています。")
        return

    if not os.path.exists(ARCHIVE_FILE_PATH):
        run_curl_command()

    print("zipファイルの展開を開始します...")
    with zipfile.ZipFile(ARCHIVE_FILE_PATH, "r") as zip_ref:
        zip_ref.extractall(EXPAND_TARGET_DIR)
    print("zipファイルの展開が完了しました。")