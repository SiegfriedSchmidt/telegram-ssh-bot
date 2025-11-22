import os
from pathlib import Path

data_folder_path = os.environ.get("DATA_FOLDER_PATH", "./data")
secret_folder_path = Path(os.environ.get("SECRET_FOLDER_PATH", "./.secret"))
if not os.path.exists(secret_folder_path):
    secret_folder_path = '../' / secret_folder_path

key_path = secret_folder_path / ".ssh_keys/id_manager"
settings_file_path = secret_folder_path / "settings.json"
