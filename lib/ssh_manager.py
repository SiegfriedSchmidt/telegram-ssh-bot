import json
from typing import Tuple, List

import paramiko
import time

from lib.config_reader import config
from lib.init import key_path
from lib.logger import ssh_logger

proj = "/home/DockerProjects"


class SSHManager:
    def __init__(self, host: str, port: str | int, username: str, key_path: str):
        self.host = host
        self.port = int(port)
        self.username = username
        self.key = paramiko.Ed25519Key.from_private_key_file(key_path)
        self.ssh: paramiko.SSHClient | None = None
        self.shell: paramiko.Channel | None = None

    def get_stats(self):
        results = self.run_multiple_commands([
            "docker ps -s --format json",
            "docker stats --no-stream --format json",
            "free -h"
        ])
        docker_ps = json.loads(f'[{','.join(results[0][0].splitlines())}]')
        docker_stats = json.loads(f'[{','.join(results[1][0].splitlines())}]')
        htop = results[2][0]
        return docker_ps, docker_stats, htop

    def get_docker_projects(self) -> List[str]:
        result, error = self.run_single_command(f"ls {proj}")
        return result.splitlines()

    def up_project(self, project_name: str) -> str:
        result, error = self.run_single_command(f"cd {proj}/{project_name} && docker compose up -d")
        return error

    def down_project(self, project_name: str) -> str:
        result, error = self.run_single_command(f"cd {proj}/{project_name} && docker compose down")
        return error

    def update(self):
        result, error = self.run_single_command(f"""
nohup sh -c '
    cd {proj}/telegram-ssh-bot &&
    docker compose pull &&
    docker compose down &&
    docker compose up -d
' >/tmp/bot_update.log 2>&1 &
""")
        return result

    # youruser ALL=(ALL) NOPASSWD: /usr/sbin/reboot
    def reboot(self):
        result, error = self.run_single_command(f"""
        nohup sh -c '
            sudo reboot
        ' >/tmp/bot_update.log 2>&1 &
        """)
        return result

    def docker_prune(self):
        result, error = self.run_single_command("docker system prune -f")
        return result

    def connect(self) -> None:
        if self.ssh is None:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, self.port, username=self.username, pkey=self.key)

    def disconnect(self) -> None:
        if self.ssh:
            self.ssh.close()
            self.ssh = None
            self.shell = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def run_multiple_commands(self, commands: List[str], delay: float = 1) -> List[Tuple[str, str]]:
        if not commands:
            return []

        results = []
        with self:
            for i, command in enumerate(commands):
                ssh_logger.info(f"Running command: {command}")
                try:
                    stdin, stdout, stderr = self.ssh.exec_command(command)

                    # Add timeout to prevent hanging
                    stdout.channel.settimeout(30)

                    result = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    results.append((result, error))

                    if i < len(commands) - 1:
                        time.sleep(delay)

                except Exception as e:
                    results.append(('', f"Command failed: {str(e)}"))

        return results

    def run_single_command(self, command: str) -> Tuple[str, str]:
        return self.run_multiple_commands([command])[0]


if __name__ == '__main__':
    ssh_manager = SSHManager(
        config.host.get_secret_value(),
        config.port.get_secret_value(),
        config.user.get_secret_value(),
        key_path
    )
    ssh_manager.get_stats()
