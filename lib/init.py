import os
from pathlib import Path

bot_version = '1.0v alpha'

secret_folder_path = Path(os.environ.get("SECRET_FOLDER_PATH", "./.secret"))
data_folder_path = Path(os.environ.get("DATA_FOLDER_PATH", "./data"))
assets_folder_path = Path(os.environ.get("ASSETS_FOLDER_PATH", "./assets"))

for _ in range(2):
    if not os.path.exists(secret_folder_path):
        secret_folder_path = '../' / secret_folder_path
    if not os.path.exists(data_folder_path):
        data_folder_path = '../' / data_folder_path
    if not os.path.exists(assets_folder_path):
        assets_folder_path = '../' / assets_folder_path

fonts_folder_path = assets_folder_path / "fonts"
keys_folder_path = secret_folder_path / ".ssh_keys"
settings_file_path = secret_folder_path / "settings.json"
persistent_file_path = data_folder_path / "persistent_data.json"
