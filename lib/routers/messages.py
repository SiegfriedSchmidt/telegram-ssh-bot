from aiogram import Router, F, types
from aiogram.types import ReactionTypeEmoji

from lib.config_reader import config

router = Router()


@router.message(F.text.contains('admin'))
async def admin_message(message: types.Message):
    for chat_id in config.notification_ids:
        await message.bot.send_message(chat_id, f'{message.from_user.username} summoning you!')
    return await message.reply(f"Кто-то сказал admin?!")


@router.message(F.text.lower().contains('bipki') | F.text.lower().contains('бипки'))
async def bipki_message(message: types.Message):
    await message.react([ReactionTypeEmoji(emoji='🔥')])
