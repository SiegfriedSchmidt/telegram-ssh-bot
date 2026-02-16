from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from lib.database import Database
from lib.logger import main_logger


class LoggerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        user_data = data['event_from_user']
        database: Database = data['database']

        main_logger.info(
            f"id: {user_data.id}, "
            f"Username: {user_data.username}, "
            f"message: {event.text}"
        )

        await handler(event, data)
