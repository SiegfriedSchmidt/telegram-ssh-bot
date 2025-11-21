from aiogram import Router, F, types

from lib.config_reader import config

router = Router()


@router.message(F.text.contains('admin'))
async def new_message(message: types.Message):
    for chat_id in config.notification_ids:
        await message.bot.send_message(chat_id.get_secret_value(), f'{message.from_user.username} summoning you!')
    return await message.reply(f"Кто-то сказал admin?!")
