import asyncio
import nest_asyncio
import signal
from typing import Any, Callable, Coroutine
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# from lib.api.joke_api import get_joke
from lib.api.meme_api import get_meme
from lib.bot_commands import bot_commands
from lib.config_reader import config
from lib.database import Database
from lib.handlers import commands, messages, public_commands, errors, admin
from lib.logger import main_logger
from lib.middlewares.access_middleware import AccessMiddleware
from lib.middlewares.logger_middleware import LoggerMiddleware
from lib.storage import storage

nest_asyncio.apply()


class DispatcherOnShutdown(Dispatcher):
    def __init__(self, on_shutdown: Callable[[], Coroutine], **kwargs: Any):
        self.on_shutdown = on_shutdown
        super().__init__(**kwargs)

    def _signal_stop_polling(self, sig: signal.Signals) -> None:
        asyncio.run(self.on_shutdown())
        super()._signal_stop_polling(sig)


async def notification(message: str, bot: Bot):
    main_logger.info(message)
    await bot.send_message(int(config.group_id.get_secret_value()), message, parse_mode=None)


async def on_day_start(bot: Bot):
    # joke = await get_joke('Dark')
    # message = f'Daily joke:\n\n{joke}'
    # await bot.send_message(int(config.group_id.get_secret_value()), message, parse_mode=None)

    group_id = int(config.group_id.get_secret_value())
    try:
        url, caption = await get_meme()
        try:
            if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                await bot.send_photo(group_id, url, caption=caption)
            elif url.endswith('.gif'):
                await bot.send_animation(group_id, url, caption=caption)
            elif url.endswith(('.mp4', '.gifv', '.webm')):
                await bot.send_video(group_id, url, caption=caption)
        except TelegramBadRequest:
            await asyncio.sleep(1)
            await bot.send_message(group_id, f"{url}\n\n{caption}", disable_web_page_preview=False)
    except Exception as e:
        main_logger.exception(e)

    main_logger.info("Day start function executed.")


async def main():
    # logging.basicConfig(level=logging.DEBUG)
    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=None))
    database = Database()

    async def on_shutdown():
        if not storage.notification_enabled:
            return

        await notification("Bot stopped.", bot)

    async def on_start():
        if not storage.notification_enabled:
            return

        containers_json = database.ssh_manager.get_running_containers()
        nextcloud_running = False
        for c in containers_json:
            if c["Image"] == 'nextcloud':
                nextcloud_running = True
        start_message = "Bot started." + (
            " Nextcloud is NOT running. Launch it via '/up nextcloud'." if not nextcloud_running else ''
        )
        await notification(start_message, bot)

    # scheduler
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour=11, minute=0)
    scheduler.add_job(on_day_start, trigger, args=(bot,))
    scheduler.start()

    # dispatcher
    dp = DispatcherOnShutdown(on_shutdown)

    # middlewares
    dp.message.middleware(LoggerMiddleware())
    dp.message.middleware(AccessMiddleware())

    # group router
    group_router = Router()
    group_router.message.filter(F.chat.type.in_(["group", "supergroup"]),
                                F.chat.id == int(config.group_id.get_secret_value()))
    group_router.include_router(commands.router)
    group_router.include_router(messages.router)

    # include routers
    dp.include_router(errors.router)
    dp.include_router(public_commands.router)
    dp.include_router(admin.router)
    dp.include_router(group_router)

    await on_start()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(bot_commands)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), database=database)


def start_bot():
    asyncio.run(main())
