from lib.config_reader import config
from lib.init import key_path
from lib.ssh_manager import SSHManager


def main():
    ssh = SSHManager(
        config.host.get_secret_value(),
        config.port.get_secret_value(),
        config.user.get_secret_value(),
        key_path
    )

    result, error = ssh.run_ssh_command("docker ps -a")
    print(result)


if __name__ == '__main__':
    main()
