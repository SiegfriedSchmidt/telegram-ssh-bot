import asyncio

import aiohttp

joke_types = {'Any', 'Misc', 'Programming', 'Dark', 'Pun', 'Spooky', 'Christmas'}
joke_url = 'https://v2.jokeapi.dev/joke'

# https://v2.jokeapi.dev/#getting-started
params = {
    'format': 'txt',
    'lang': 'en',
}


class JokeError(Exception):
    pass


class InvalidJokeType(JokeError):
    def __init__(self, joke_type: str):
        super().__init__(f"Invalid joke type: {joke_type}. Allowed joke types: {', '.join(joke_types)}.")


class JokeAPIError(JokeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Joke API error: {status}.")


async def get_joke(joke_type: str = None) -> str:
    if joke_type is None:
        joke_type = 'Any'

    if joke_type not in joke_types:
        raise InvalidJokeType(joke_type)

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{joke_url}/{joke_type}', params=params | {}) as rs:
            if rs.status != 200:
                raise JokeAPIError(rs.status)

            text = await rs.text()
            return text


async def main():
    joke = await get_joke()
    print(joke)


if __name__ == '__main__':
    asyncio.run(main())
