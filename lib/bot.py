import asyncio
from typing import Any, Callable, Coroutine
import nest_asyncio
import signal
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties

from lib.config_reader import config
from lib.database import Database
from lib.handlers import commands, messages, public_commands
from lib.logger import main_logger
from lib.middlewares.loggerMiddleware import LoggerMiddleware

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


async def main():
    # logging.basicConfig(level=logging.DEBUG)
    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode='HTML'))
    database = Database()

    async def on_shutdown():
        await notification("Bot stopped.", bot)

    async def on_start():
        await notification("Bot started.", bot)

    dp = DispatcherOnShutdown(on_shutdown)

    dp.message.middleware(LoggerMiddleware())

    group_router = Router()
    group_router.message.filter(F.chat.type.in_(["group", "supergroup"]),
                                F.chat.id == int(config.group_id.get_secret_value()))
    group_router.include_router(commands.router)
    group_router.include_router(messages.router)

    dp.include_router(public_commands.router)
    dp.include_router(group_router)

    await on_start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), database=database)


def start_bot():
    asyncio.run(main())
