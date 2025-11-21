import json
from typing import Tuple, List

import paramiko

from lib.config_reader import config
from lib.init import key_path

proj = "/home/DockerProjects"


class SSHManager:
    def __init__(self, host: str, port: str | int, user: str, key_path: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.key = paramiko.Ed25519Key.from_private_key_file(key_path)

    def get_docker_ps(self) -> List[str]:
        result, error = self.run_ssh_command("docker ps -s --format json")
        containers = json.loads(f'[{','.join(result.splitlines())}]')
        pad = len(max(containers, key=lambda c: len(c['Image']))['Image'])
        return [f"{c["Image"].ljust(pad, ' ')} {c['Names']}" for c in containers]

    def get_docker_projects(self) -> List[str]:
        result, error = self.run_ssh_command(f"ls {proj}")
        return result.splitlines()

    def up_project(self, project_name: str) -> str:
        result, error = self.run_ssh_command(f"cd {proj}/{project_name} && docker compose up -d")
        return error

    def down_project(self, project_name: str) -> str:
        result, error = self.run_ssh_command(f"cd {proj}/{project_name} && docker compose down")
        return error

    def update(self):
        result, error = self.run_ssh_command(f"""
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
        result, error = self.run_ssh_command(f"""
        nohup sh -c '
            sudo reboot
        ' >/tmp/bot_update.log 2>&1 &
        """)
        return result

    def docker_prune(self):
        result, error = self.run_ssh_command("docker system prune -f")
        return result

    def htop(self):
        result, error = self.run_ssh_command("free -h")
        return result

    def run_ssh_command(self, command: str) -> Tuple[str, str]:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, self.port, username=self.user, pkey=self.key)

        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()
        error = stderr.read().decode()

        ssh.close()

        return result, error


if __name__ == '__main__':
    ssh_manager = SSHManager(
        config.host.get_secret_value(),
        config.port.get_secret_value(),
        config.user.get_secret_value(),
        key_path
    )
    ssh_manager.get_docker_projects()
