import os
from pathlib import Path

data_folder_path = Path(os.environ.get("DATA_FOLDER_PATH", "./data"))
secret_folder_path = Path(os.environ.get("SECRET_FOLDER_PATH", "./.secret"))
if not os.path.exists(secret_folder_path):
    secret_folder_path = '../' / secret_folder_path
if not os.path.exists(secret_folder_path):
    secret_folder_path = '../' / secret_folder_path
if not os.path.exists(data_folder_path):
    data_folder_path = '../' / data_folder_path

keys_folder_path = secret_folder_path / ".ssh_keys"
settings_file_path = secret_folder_path / "settings.json"
persistent_file_path = data_folder_path / "persistent_data.json"
videos_folder_path = data_folder_path / 'videos'
