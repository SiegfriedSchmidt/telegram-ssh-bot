import json
from typing import Tuple, List

import paramiko
import time

from lib.config_reader import config
from lib.init import key_path
from lib.logger import ssh_logger
from lib.ssh_session import SSHSession

proj = "/home/DockerProjects"


class SSHManager:
    def __init__(self, host: str, port: str | int, username: str, key_path: str):
        self.host = host
        self.port = int(port)
        self.username = username
        self.key = paramiko.Ed25519Key.from_private_key_file(key_path)
        self.ssh: paramiko.SSHClient | None = None
        ssh_logger.info("SSH manager created!")

    def get_running_containers(self) -> dict:
        result = self.run_single_command("docker ps -s --format json")
        return json.loads(f'[{','.join(result[0].splitlines())}]')

    def get_stats(self) -> tuple[dict, dict, str, str, str]:
        results = self.run_multiple_commands([
            "docker ps -s --format json",
            "docker stats --no-stream --format json",
            "free -h | awk '/Mem:/ {printf \"%s/%s\n\", $3, $2}'",
            "top -bn1 | grep \"Cpu(s)\" | awk '{print 100 - $8 \"%\"}'",
            "uptime -p"
        ])
        docker_ps = json.loads(f'[{','.join(results[0][0].splitlines())}]')
        docker_stats = json.loads(f'[{','.join(results[1][0].splitlines())}]')
        return docker_ps, docker_stats, results[2][0], results[3][0], results[4][0]

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

    def curl(self, args: str):
        return self.run_single_command(f"curl {args}")

    def openconnect(self, action: str):
        return self.run_single_command(f"sudo systemctl {action} openconnect.service")

    def connect(self) -> None:
        if self.ssh is None:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, self.port, username=self.username, pkey=self.key)

    def disconnect(self) -> None:
        if self.ssh:
            self.ssh.close()
            self.ssh = None

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

    def interactive_session(self):
        return SSHSession(self.host, self.port, self.username, key_path)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __del__(self):
        self.disconnect()
        ssh_logger.info("SSH manager destroyed!")


if __name__ == '__main__':
    ssh_manager = SSHManager(
        config.host.get_secret_value(),
        config.port.get_secret_value(),
        config.user.get_secret_value(),
        key_path
    )
    ssh_manager.get_stats()
