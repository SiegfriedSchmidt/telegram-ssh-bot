import asyncio
from google import genai
from google.genai import types
from pydantic import SecretStr
from lib.config_reader import config


# https://github.com/googleapis/python-genai
class GeminiApi:
    def __init__(self, gemini_api_key: SecretStr, proxy_url: str = ''):
        http_options = types.HttpOptions(
            client_args={'proxy': proxy_url},
            async_client_args={'proxy': proxy_url},
        ) if proxy_url else None

        self.client = genai.Client(
            api_key=gemini_api_key.get_secret_value(),
            http_options=http_options
        ).aio

    async def ask(self, text: str, model="gemini-2.5-flash") -> str:
        response = await self.client.models.generate_content(
            model=model,
            contents=text,
            # config=types.GenerateContentConfig(
            #     system_instruction=[
            #         'You are a helpful language translator.',
            #         'Your mission is to translate text in English to French.'
            #     ]
            # ),
        )
        return response.text


gemini_api = GeminiApi(config.gemini_api_key, config.proxy_url)


async def main():
    print(await gemini_api.ask("Explain how AI works in a few words"))


if __name__ == '__main__':
    asyncio.run(main())
