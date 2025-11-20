import paramiko


class SSHManager:
    def __init__(self, host: str, port: str | int, user: str, key_path: str):
        self.host = host
        self.port = int(port)
        self.user = user
        self.key = paramiko.Ed25519Key.from_private_key_file(key_path)

    def run_ssh_command(self, command: str):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, self.port, username=self.user, pkey=self.key)

        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()
        error = stderr.read().decode()

        ssh.close()

        return result, error
