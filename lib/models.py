from pydantic import BaseModel, SecretStr
from enum import Enum, EnumMeta


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


class RconModel(BaseModel):
    address: str
    port: str
    password: str
    rcon_logs_path: str


class HostModel(BaseModel):
    name: SecretStr
    hostname: SecretStr
    port: SecretStr
    username: SecretStr
    key_name: SecretStr
    docker_projects_path: str
    rcon: RconModel | None = None


class DockerUpdateModel(BaseModel):
    host: str
    project_name: str

    def __str__(self) -> str:
        return f'{self.host}-{self.project_name}'

    def to_str(self) -> str:
        return str(self)


class UserModel(BaseModel):
    host: str


class TerminalType(str, BaseEnum):
    text = 'text'
    image = 'image'
