import os
from pathlib import Path

secret_folder_path = Path(os.environ.get("SECRET_FOLDER_PATH", "./.secret"))

key_path = secret_folder_path / ".ssh_keys/id_manager"
settings_file_path = secret_folder_path / "settings.json"
