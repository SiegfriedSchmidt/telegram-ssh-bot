from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, JsonConfigSettingsSource
from pydantic import SecretStr
from typing import Type, Tuple, List

from lib.init import settings_file_path
from lib.models import HostModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(json_file=settings_file_path, json_file_encoding='utf-8', extra='allow')
    hosts: List[HostModel]
    main_host: SecretStr
    bot_token: SecretStr
    group_id: int
    admin_ids: List[int]
    notification_ids: List[int]
    gemini_api_key: SecretStr
    otp_secret: SecretStr
    proxy_url: str = ''

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


config = Settings()
