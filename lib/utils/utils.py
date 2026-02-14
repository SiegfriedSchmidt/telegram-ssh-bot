import json
import asyncio
from io import BytesIO
from typing import List, Iterable
from aiogram import types

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


async def run_in_thread(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


async def large_respond(message: types.Message, obj: str | Iterable[str], timeout=3, characters=2000,
                        maximum=6, **kwargs) -> bool:
    if not obj:
        await message.answer("Nothing.")
        return True
    elif isinstance(obj, str):
        if len(obj) >= characters * 4:
            await message.answer("Too large.")
            return False
        for i in range(0, len(obj), characters):
            await message.answer(obj[i:i + characters], **kwargs)
            await asyncio.sleep(timeout)
    elif isinstance(obj, Iterable):
        divided_message = []
        log = ''
        cnt = 0
        for item in obj:
            cnt += len(item)
            if cnt >= characters:
                divided_message.append(log)
                log = ''
                cnt = len(item)

            log += item

        if log:
            divided_message.append(log)

        if len(divided_message) >= maximum:
            await message.answer("Too large.")
            return False

        for message in divided_message:
            await message.answer(message, **kwargs)
            await asyncio.sleep(timeout)
    else:
        await message.answer("I've get smth else than a str or Iterable.")

    return True
