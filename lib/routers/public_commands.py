from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("chat_id"))
async def chat_id(message: types.Message):
    await message.answer(str(message.chat.id))
