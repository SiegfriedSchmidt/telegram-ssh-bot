from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from lib.logger import main_logger

router = Router()


@router.errors()
async def error_handler(event: ErrorEvent):
    exception = event.exception

    if isinstance(exception, TelegramBadRequest):
        error_text = str(exception)
        if "can't parse" in error_text.lower():
            await safe_send(event.update, "Bot tried to send something weird. Skipping...")
        elif "message is empty" in error_text.lower():
            await safe_send(event.update, "Empty message – nothing to send!")
        elif "caption is too long" in error_text.lower():
            await safe_send(event.update, "That caption was too long for Telegram!")
        else:
            await safe_send(event.update, "Telegram rejected the message.")
    elif isinstance(exception, TelegramAPIError):
        await safe_send(event.update, "Telegram server is having a moment.")
    else:
        await safe_send(event.update, "Unknown error occurred.")

    main_logger.exception("Telegram error caught globally", exc_info=exception)


async def safe_send(update, text: str):
    try:
        if update.message:
            await update.message.answer(text[:4000])
        elif update.callback_query:
            await update.callback_query.message.answer(text[:4000])
    except:
        pass
