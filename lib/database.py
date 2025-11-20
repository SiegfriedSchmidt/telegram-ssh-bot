from lib.config_reader import config
from lib.init import key_path
from lib.ssh_manager import SSHManager


class User:
    def __init__(self, name: str):
        self.name = name


class Database:
    def __init__(self):
        self.users: dict[int, User] = dict()
        self.ssh_manager: SSHManager = SSHManager(
            config.host.get_secret_value(),
            config.port.get_secret_value(),
            config.user.get_secret_value(),
            key_path
        )

    def add_user(self, user_id: int, user: User):
        self.users[user_id] = user

    def get_user(self, user_id: int) -> User:
        return self.users[user_id]
