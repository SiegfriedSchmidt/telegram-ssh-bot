import asyncio
import os
from datetime import datetime, time, timedelta
from io import BytesIO
from pathlib import Path
from typing import List, Iterable, Tuple
from aiogram import types
from aiogram.filters import CommandObject


def get_file_from_str(string: str, filename: str) -> BytesIO:
    file = BytesIO(str(string).encode("utf-8"))
    file.name = filename
    return file


def get_dir_size(path: Path | str):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total


def clear_dir_contents(path: Path | str) -> List[Tuple[str, int]]:
    files: List[Tuple[str, int]] = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                files.append((entry.name, entry.stat().st_size))
                os.remove(entry.path)
            elif entry.is_dir():
                files.extend(clear_dir_contents(entry.path))
    return files


def remove_file(path: Path) -> int:
    if not path.is_file():
        raise FileNotFoundError()
    filesize = path.stat().st_size
    os.remove(path)
    return filesize


def get_args(command: CommandObject):
    return command.args.split() if command.args else []


def used_today(last_used: datetime, day_start_time: str) -> bool:
    hour, minute = map(int, day_start_time.split(":"))
    start_time = time(hour, minute)

    now = datetime.now()

    # Construct today's start time
    today_start = datetime.combine(now.date(), start_time)

    # Determine actual logical day start
    if now < today_start:
        # Day started yesterday
        day_start = today_start - timedelta(days=1)
    else:
        # Day started today
        day_start = today_start

    day_end = day_start + timedelta(days=1)

    return day_start <= last_used < day_end


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
