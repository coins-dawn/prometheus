import os
import zipfile

ARCHIVE_FILE_PATH = "data/archive.zip"
EXPAND_TARGET_DIR = "data/archive/"


def arrange_data():
    if os.path.exists(EXPAND_TARGET_DIR):
        print("データはすでに展開されています。")
        return

    print("zipファイルの展開を開始します...")
    with zipfile.ZipFile(ARCHIVE_FILE_PATH, "r") as zip_ref:
        zip_ref.extractall(EXPAND_TARGET_DIR)
    print("zipファイルの展開が完了しました。")
