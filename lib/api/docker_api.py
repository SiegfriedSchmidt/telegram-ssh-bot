import asyncio
import aiohttp


async def get_latest_image_digest(image_repository: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://hub.docker.com/v2/repositories/{image_repository}/tags/latest") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("digest", None)
    except aiohttp.ClientError:
        pass
    return None


if __name__ == '__main__':
    print(asyncio.run(get_latest_image_digest("siegfriedschmidt/telegram-ssh-bot")))
