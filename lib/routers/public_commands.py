from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("chat_id"))
async def chat_id_cmd(message: types.Message):
    await message.answer(str(message.chat.id))


@router.message(Command("user_id"))
async def user_id_cmd(message: types.Message):
    await message.answer(str(message.from_user.id))
