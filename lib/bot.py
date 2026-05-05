import asyncio
import nest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from lib.bot_commands import set_bot_commands
from lib.config_reader import config
from lib.init import bot_version
from lib.routers import public_commands, errors, admin_commands, ssh_session
from lib.logger import main_logger
from lib.middlewares.logger_middleware import LoggerMiddleware
from lib.ssh_manager import ssh_manager
from lib.storage import storage

nest_asyncio.apply()


async def notification(message: str, bot: Bot, parse_mode=None):
    main_logger.info(message)
    if storage.notifications_enabled:
        await bot.send_message(config.main_group_id, message, parse_mode=parse_mode)


async def on_startup(bot: Bot) -> None:
    # start message
    start_message = f"Bot {bot_version} started."

    # startup docker checks
    if storage.startup_docker_checks:
        containers_json = ssh_manager[config.main_host.get_secret_value()].get_running_containers()
        nextcloud_running = False
        for c in containers_json:
            if c["Image"] == 'nextcloud':
                nextcloud_running = True
        start_message += '' if nextcloud_running else " Nextcloud is NOT running. Launch it via '/up nextcloud'."

    await notification(start_message, bot, parse_mode="HTML")


async def on_shutdown(bot: Bot) -> None:
    await notification("Bot stopped.", bot)


async def main():
    # logging.basicConfig(level=logging.DEBUG)
    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=None, disable_notification=True),
        session=AiohttpSession(proxy=config.proxy_url if config.proxy_url else None)
    )

    # dispatcher
    dp = Dispatcher()

    # register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # middlewares
    dp.message.middleware(LoggerMiddleware())

    # routers
    dp.include_routers(
        errors.router,
        public_commands.router,
        admin_commands.router,
        ssh_session.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def start_bot():
    asyncio.run(main())
