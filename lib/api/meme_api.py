import asyncio
from typing import Tuple

import aiohttp

from lib.config_reader import config

# https://github.com/D3vd/Meme_Api
meme_url = 'https://meme-api.com/gimme'


class MemeError(Exception):
    pass


class InvalidMemeSubreddit(MemeError):
    def __init__(self, subreddit: str):
        self.subreddit = subreddit
        super().__init__(f"Subreddit should not be a digit.")


class MemeApiError(MemeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Meme API error: {status}.")


async def get_meme(subreddit: str = None) -> Tuple[str, str]:
    if subreddit is None:
        subreddit = ''

    if subreddit.isdigit():
        raise InvalidMemeSubreddit(subreddit)

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{meme_url}/{subreddit}', proxy=config.proxy_url) as rs:
            if rs.status == 404:
                raise MemeApiError(rs.status)

            data = await rs.json()
            if 'code' in data:
                raise MemeApiError(data['code'])

            return data["url"], data["title"]


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://eth0.me', proxy=config.proxy_url) as rs:
            print(await rs.text())

    # meme = await get_meme()
    # print(meme)


if __name__ == '__main__':
    asyncio.run(main())
