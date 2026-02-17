from collections.abc import Callable
from io import BytesIO
from typing import Awaitable

import paramiko
import time
import asyncio
from lib.config_reader import config
from lib.emulated_terminal import EmulatedTerminal
from lib.init import keys_folder_path
from lib.logger import ssh_logger
from lib.models import HostModel, TerminalType

SPECIAL_KEYS = {
    # Arrow keys
    'up': '\x1b[A',
    'down': '\x1b[B',
    'right': '\x1b[C',
    'left': '\x1b[D',

    # Navigation keys
    'home': '\x1b[H',
    'end': '\x1b[F',
    'pgup': '\x1b[5~',
    'pgdown': '\x1b[6~',
    'insert': '\x1b[2~',
    'delete': '\x1b[3~',

    # Function keys
    'f1': '\x1bOP',
    'f2': '\x1bOQ',
    'f3': '\x1bOR',
    'f4': '\x1bOS',
    'f5': '\x1b[15~',
    'f6': '\x1b[17~',
    'f7': '\x1b[18~',
    'f8': '\x1b[19~',
    'f9': '\x1b[20~',
    'f10': '\x1b[21~',
    'f11': '\x1b[23~',
    'f12': '\x1b[24~',

    # Ctrl + letter combinations
    'ctrl_a': '\x01',  # Ctrl+A (ASCII 1)
    'ctrl_b': '\x02',  # Ctrl+B
    'ctrl_c': '\x03',  # Ctrl+C (interrupt)
    'ctrl_d': '\x04',  # Ctrl+D (EOF)
    'ctrl_e': '\x05',  # Ctrl+E (end of line)
    'ctrl_f': '\x06',  # Ctrl+F (forward char)
    'ctrl_g': '\x07',  # Ctrl+G (bell)
    'ctrl_h': '\x08',  # Ctrl+H (backspace)
    'ctrl_i': '\x09',  # Ctrl+I (tab)
    'ctrl_j': '\x0a',  # Ctrl+J (newline)
    'ctrl_k': '\x0b',  # Ctrl+K (kill line forward)
    'ctrl_l': '\x0c',  # Ctrl+L (clear screen)
    'ctrl_m': '\x0d',  # Ctrl+M (carriage return)
    'ctrl_n': '\x0e',  # Ctrl+N (next line)
    'ctrl_o': '\x0f',  # Ctrl+O
    'ctrl_p': '\x10',  # Ctrl+P (previous line)
    'ctrl_q': '\x11',  # Ctrl+Q (resume output)
    'ctrl_r': '\x12',  # Ctrl+R (reverse search)
    'ctrl_s': '\x13',  # Ctrl+S (stop output)
    'ctrl_t': '\x14',  # Ctrl+T (transpose chars)
    'ctrl_u': '\x15',  # Ctrl+U (kill line backward)
    'ctrl_v': '\x16',  # Ctrl+V (literal next)
    'ctrl_w': '\x17',  # Ctrl+W (kill word backward)
    'ctrl_x': '\x18',  # Ctrl+X
    'ctrl_y': '\x19',  # Ctrl+Y (yank)
    'ctrl_z': '\x1a',  # Ctrl+Z (suspend)

    # Ctrl + special combinations
    'ctrl_[': '\x1b',  # Ctrl+[ (ESC)
    'ctrl_\\': '\x1c',  # Ctrl+\
    'ctrl_]': '\x1d',  # Ctrl+]
    'ctrl_^': '\x1e',  # Ctrl+^
    'ctrl_/': '\x1f',  # Ctrl+/

    # Alt combinations (ESC + key)
    'alt_a': '\x1ba',
    'alt_b': '\x1bb',
    'alt_c': '\x1bc',
    'alt_d': '\x1bd',
    'alt_e': '\x1be',
    'alt_f': '\x1bf',
    'alt_g': '\x1bg',
    'alt_h': '\x1bh',
    'alt_i': '\x1bi',
    'alt_j': '\x1bj',
    'alt_k': '\x1bk',
    'alt_l': '\x1bl',
    'alt_m': '\x1bm',
    'alt_n': '\x1bn',
    'alt_o': '\x1bo',
    'alt_p': '\x1bp',
    'alt_q': '\x1bq',
    'alt_r': '\x1br',
    'alt_s': '\x1bs',
    'alt_t': '\x1bt',
    'alt_u': '\x1bu',
    'alt_v': '\x1bv',
    'alt_w': '\x1bw',
    'alt_x': '\x1bx',
    'alt_y': '\x1by',
    'alt_z': '\x1bz',

    # Alt + special
    'alt_enter': '\x1b\r',
    'alt_space': '\x1b ',
    'alt_tab': '\x1b\t',
    'alt_backspace': '\x1b\x7f',

    # Other common keys
    'tab': '\t',
    'enter': '\r',
    'backspace': '\x7f',
    'escape': '\x1b',
    'space': ' ',

    # Terminal control
    'eof': '\x04',  # Ctrl+D
    'eot': '\x04',  # End of transmission
    'ack': '\x06',  # Acknowledge
    'bel': '\x07',  # Bell
    'bs': '\x08',  # Backspace
    'ht': '\x09',  # Horizontal tab
    'lf': '\x0a',  # Line feed
    'vt': '\x0b',  # Vertical tab
    'ff': '\x0c',  # Form feed
    'cr': '\x0d',  # Carriage return
    'so': '\x0e',  # Shift out
    'si': '\x0f',  # Shift in
    'dc1': '\x11',  # Device control 1 (XON)
    'dc3': '\x13',  # Device control 3 (XOFF)
    'can': '\x18',  # Cancel
    'em': '\x19',  # End of medium
    'sub': '\x1a',  # Substitute
    'esc': '\x1b',  # Escape
    'fs': '\x1c',  # File separator
    'gs': '\x1d',  # Group separator
    'rs': '\x1e',  # Record separator
    'us': '\x1f',  # Unit separator
    'del': '\x7f',  # Delete
}


async def async_print(*args, **kwargs):
    print(*args, **kwargs)


class SSHInteractiveSession:
    def __init__(self, host: HostModel, terminal_type: TerminalType = TerminalType.text, width: int = 120,
                 height: int = 40):
        self.name = host.name.get_secret_value()
        self.hostname = host.hostname.get_secret_value()
        self.port = int(host.port.get_secret_value())
        self.username = host.username.get_secret_value()
        self.key = paramiko.Ed25519Key.from_private_key_file(keys_folder_path / host.key_name.get_secret_value())
        self.terminal_type = terminal_type
        self.emulated_terminal = EmulatedTerminal(width, height)
        self.client: paramiko.SSHClient | None = None
        self.channel: paramiko.channel.Channel | None = None
        self.with_callback = async_print
        self._connected = False

    async def connect(self, callback: Callable[[str | BytesIO], Awaitable[None]]) -> None:
        if self._connected:
            return

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(self.hostname, self.port, username=self.username, pkey=self.key)

            self.channel = self.client.invoke_shell(
                term="xterm-256color",  # "vt100", "xterm", "xterm-256color"
                width=self.emulated_terminal.width,
                height=self.emulated_terminal.height
            )

            # Give remote time to send banner / MOTD / prompt
            time.sleep(1)

            self._connected = True
            asyncio.create_task(self._read_output(callback))
            ssh_logger.info(f"Interactive SSH session for {self.name} established!")
        except Exception as e:
            ssh_logger.error(f"Connection failed: {e}", exc_info=True)
            self.close()
            raise

    async def _read_output(self, callback: Callable[[str | BytesIO], Awaitable[None]], polling: float = 1) -> None:
        if not self.channel:
            return

        while True:
            if not self._connected:
                break

            if self.channel.recv_ready():
                self.emulated_terminal.feed(self.channel.recv(8192))

                if self.channel.recv_stderr_ready():
                    self.emulated_terminal.feed(self.channel.recv_stderr(4096))

                if self.terminal_type == TerminalType.text:
                    await callback(self.emulated_terminal.text())
                else:
                    await callback(self.emulated_terminal.render())

            await asyncio.sleep(polling)

    def send_command(self, command: str) -> None:
        if not self.channel or self.channel.closed:
            raise RuntimeError("No active shell channel")

        lower = command.lower()
        if lower in SPECIAL_KEYS:
            self.channel.send(SPECIAL_KEYS[lower])
        else:
            self.channel.send((command.rstrip() + "\n").encode("utf-8"))
        ssh_logger.info(f"Sent command to {self.name}: {command}")

    def close(self) -> None:
        if not self._connected:
            return

        if self.channel and not self.channel.closed:
            self.channel.close()
        if self.client:
            self.client.close()

        self._connected = False
        ssh_logger.info(f"Interactive SSH session for {self.name} closed!")

    async def __aenter__(self):
        await self.connect(self.with_callback)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


async def main() -> None:
    async with SSHInteractiveSession(config.hosts[0]) as session:
        session.send_command("echo $TERM")
        session.send_command("ls -la --color=always")
        session.send_command("echo -e '\\033[38;5;196mHELLO\\033[0m'")
        session.send_command("whoami")
        session.send_command("uptime")
        session.send_command("pwd")
        session.send_command("cd /home/DockerProjects")
        session.send_command("pwd")
        session.send_command("htop")
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
