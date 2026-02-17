from pydantic import BaseModel, SecretStr


class HostModel(BaseModel):
    name: SecretStr
    hostname: SecretStr
    port: SecretStr
    username: SecretStr
    key_name: SecretStr


class UserModel(BaseModel):
    host: str
