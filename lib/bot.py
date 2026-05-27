import asyncio
import nest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from lib.api.docker_api import get_latest_image_digest
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


async def docker_image_update_check(bot: Bot):
    docker_updates_hashes = storage.docker_updates_hashes
    whole_updating_message_list = []
    for repository, docker_update_list in config.docker_updates.items():
        updating_message_list = []

        if (latest_sha := await get_latest_image_digest(repository)) is None:
            continue

        for docker_update in docker_update_list:
            docker_update_str = docker_update.to_str()
            if latest_sha != docker_updates_hashes.get(docker_update_str, ""):
                docker_updates_hashes[docker_update_str] = latest_sha
                updating_message_list.append(
                    f"      Host: <b>{docker_update.host}</b>, Project: <b>{docker_update.project_name}</b>"
                )
                ssh_manager[docker_update.host].update(docker_update.project_name)

        if updating_message_list:
            whole_updating_message_list.append(
                f"Image <b>{repository}</b> update detected ({latest_sha[-7:]})\n"
                f"Updating to latest:\n" + "\n".join(updating_message_list)
            )

    if whole_updating_message_list:
        await notification("\n\n".join(whole_updating_message_list), bot, parse_mode="HTML")

    storage.docker_updates_hashes = docker_updates_hashes


async def main():
    # logging.basicConfig(level=logging.DEBUG)
    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=None, disable_notification=True),
        session=AiohttpSession(proxy=config.proxy_url if config.proxy_url else None)
    )

    # scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        docker_image_update_check,
        IntervalTrigger(seconds=storage.docker_image_update_check_interval_seconds), args=(bot,)
    )
    scheduler.start()

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
