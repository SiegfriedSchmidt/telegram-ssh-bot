from aiogram import Router, F, types

router = Router()

@router.message(F.text.contains('admin'))
async def new_message(message: types.Message):
    await message.reply(f"Кто-то сказал admin?!")
