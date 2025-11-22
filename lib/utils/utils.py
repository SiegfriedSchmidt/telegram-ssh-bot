import json
from io import BytesIO
from typing import List

from aiogram.filters import CommandObject


def get_file_from_str(string: str, filename: str) -> BytesIO:
    file = BytesIO(str(string).encode("utf-8"))
    file.name = filename
    return file


def save_with_attributes(instances: List[object], filename: str):
    data = [obj.to_dict() for obj in instances]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_with_attributes(filename: str, cls):
    with open(filename, 'r') as f:
        data = json.load(f)

    return [cls.from_dict(item) for item in data]


def get_args(command: CommandObject):
    return command.args.split() if command.args else []
