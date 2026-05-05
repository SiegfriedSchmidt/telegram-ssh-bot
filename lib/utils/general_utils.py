import asyncio
from io import BytesIO
from typing import ParamSpec, TypeVar, Callable


def get_file_from_str(string: str, filename: str) -> BytesIO:
    file = BytesIO(str(string).encode("utf-8"))
    file.name = filename
    return file


P = ParamSpec("P")
R = TypeVar("R")


async def run_in_thread(func: Callable[P, R], *args: P.args) -> R:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)
