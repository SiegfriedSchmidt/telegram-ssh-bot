from pydantic import field_validator
from lib.models import UserModel
from lib.ssh_manager import ssh_manager
from lib.config_reader import config


class User(UserModel, validate_assignment=True):
    @field_validator('host', mode='before')
    @classmethod
    def validate_host(cls, value: str):
        if value not in ssh_manager.get_hosts():
            raise KeyError(f'Host {value} does not exist!')
        return value


class TemporalStorage:
    def __init__(self):
        self._users: dict[int, User] = dict()

    def get_user(self, user_id: int) -> User:
        if user_id not in self._users:
            self._users[user_id] = User(host=config.main_host.get_secret_value())

        return self._users[user_id]


temporal_storage = TemporalStorage()
