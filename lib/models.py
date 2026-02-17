from enum import Enum, EnumMeta

from pydantic import BaseModel, SecretStr


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


class HostModel(BaseModel):
    name: SecretStr
    hostname: SecretStr
    port: SecretStr
    username: SecretStr
    key_name: SecretStr


class UserModel(BaseModel):
    host: str


class TerminalType(str, BaseEnum):
    text = 'text'
    image = 'image'
