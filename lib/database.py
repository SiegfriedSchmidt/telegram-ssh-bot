from lib.models import UserModel
from lib.ssh_manager import ssh_manager
from lib.config_reader import config


class Database:
    def __init__(self):
        self.users: dict[int, UserModel] = dict()

    def set_host(self, user_id: int, host: str) -> bool:
        if host in ssh_manager.get_hosts():
            self.users[user_id] = UserModel(host=host)
            return True
        return False

    def get_host(self, user_id: int) -> str:
        if user_id not in self.users:
            self.users[user_id] = UserModel(host=config.main_host.get_secret_value())
        return self.users[user_id].host
