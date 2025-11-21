from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command("chat_id"))
async def chat_id(message: types.Message, state: FSMContext):
    await message.answer(str(message.chat.id))
