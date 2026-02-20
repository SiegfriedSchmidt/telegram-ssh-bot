from aiogram.types import BotCommand

bot_commands = [
    BotCommand(command='h', description='help message'),
    BotCommand(command='projects', description='show all docker projects'),
    BotCommand(command='up', description='{project_name:required} - start docker project'),
    BotCommand(command='down', description='{project_name:required} - stop docker project'),
    BotCommand(command='update', description='update bot image'),
    BotCommand(command='reboot', description='reboot machine'),
    BotCommand(command='prune', description='remove unused docker containers'),
    BotCommand(command='stats', description='host statistics'),
    BotCommand(command='upload_faq', description='upload faq file'),
    BotCommand(command='faq', description='get faq file'),
    BotCommand(command='joke', description='{joke_type:optional} - get joke'),
    BotCommand(command='meme', description='{subreddit:optional} - get meme from reddit'),
    BotCommand(command='logs', description='get logs'),
    BotCommand(command='ask', description='{prompt:required} - ask AI'),
    BotCommand(command='curl', description='curl command'),
    BotCommand(command='geoip', description='{ip:required} - get geoip'),
    BotCommand(command='torip', description='get tor geoip'),
    BotCommand(command='openconnect', description='{status|restart|stop|start:required} manage openconnect service'),
    BotCommand(command='del', description='delete replied message'),
    BotCommand(command='gamble', description='{bet: optional} some gambling'),
    BotCommand(command='balance', description='show gambling balance'),
    BotCommand(command='transfer', description='{amount: required, username: optional} - make transfer'),
    BotCommand(command='access', description='{otp_code:required} get privileged access'),
    BotCommand(command='activate', description='{terminal_type:optional} activate ssh session in text|image terminal'),
    BotCommand(command='deactivate', description='deactivate ssh session'),
    BotCommand(
        command='download',
        description='{url:optional} - download video, if url not provided, you should reply to message containing url'
    ),
    BotCommand(command='clear_videos', description='clear downloaded videos'),
    BotCommand(
        command='delete_video',
        description='{filename:optional} - delete video, if filename not provided, you should reply to message containing filename'
    ),
    BotCommand(command='switch', description='switch to another ssh host'),
]

text_bot_commands = '\n'.join([f"/{c.command} {c.description}" for c in bot_commands])
