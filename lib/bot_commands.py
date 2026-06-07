from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChatMember
from lib.config_reader import config

bot_admin_commands = [
    BotCommand(command='h', description='help message'),
    BotCommand(command='projects', description='show all docker projects'),
    BotCommand(command='up', description='{project_name:required} - start docker project'),
    BotCommand(command='down', description='{project_name:required} - stop docker project'),
    BotCommand(command='update', description='{project_name:optional} update bot image'),
    BotCommand(command='access', description='{otp_code:required} get privileged access'),
    BotCommand(command='geoip', description='{ip:required} - get geoip'),
    BotCommand(command='check_ip', description='check ip'),
    BotCommand(command='reboot', description='reboot machine'),
    BotCommand(command='prune', description='remove unused docker containers'),
    BotCommand(command='stats', description='host statistics'),
    BotCommand(command='logs', description='get logs'),
    BotCommand(command='curl', description='curl command'),
    BotCommand(command='openconnect', description='{status|restart|stop|start:required} manage openconnect service'),
    BotCommand(command='activate', description='{terminal_type:optional} activate ssh session in text|image terminal'),
    BotCommand(command='deactivate', description='deactivate ssh session'),
    BotCommand(command='switch', description='switch to another ssh host'),
    BotCommand(command='wol', description='{mac: required} wake on lan'),
    BotCommand(command='follow_file', description='{location: required} follow file'),
    BotCommand(command='unfollow_file', description='stop following current file'),
    BotCommand(command='rcon_follow', description='follow rcon logs file'),
    BotCommand(command='rcon', description='execute rcon command'),
]


def commands_to_text(commands: list[BotCommand]):
    return '\n'.join([f"/{c.command} {c.description}" for c in commands])


text_bot_admin_commands = commands_to_text(bot_admin_commands)


async def set_bot_commands(bot: Bot):
    for group_id in config.group_ids:
        for admin_id in config.admin_ids:
            scope = BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id)
            await bot.set_my_commands(bot_admin_commands, scope=scope)
