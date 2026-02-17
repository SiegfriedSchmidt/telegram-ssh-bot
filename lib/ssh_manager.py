from typing import List
from lib.config_reader import config
from lib.models import HostModel, TerminalType
from lib.ssh_commands import SSHCommands
from lib.ssh_interactive_session import SSHInteractiveSession


class SSHManager:
    def __init__(self, hosts: List[HostModel]):
        self._hosts = {host.name.get_secret_value(): host for host in hosts}
        self._commands = {host.name.get_secret_value(): SSHCommands(host) for host in hosts}

    def __getitem__(self, name: str) -> SSHCommands:
        if name not in self._commands:
            raise KeyError(name)
        return self._commands[name]

    def interactive_session(self, name: str, terminal_type: TerminalType) -> SSHInteractiveSession:
        if name not in self._hosts:
            raise KeyError(name)
        if terminal_type == TerminalType.text:
            width, height = 40, 24
        else:
            width, height = 120, 40
        return SSHInteractiveSession(self._hosts[name], terminal_type, width, height)

    def get_hosts(self):
        return list(self._hosts.keys())


ssh_manager = SSHManager(config.hosts)
