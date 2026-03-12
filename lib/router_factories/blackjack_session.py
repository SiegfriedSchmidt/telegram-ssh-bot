from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from lib.blackjack import Blackjack
from lib.states.blackjack_state import BlackjackState


def create_router():
    router = Router()
    router.message.filter(BlackjackState.blackjack_activated)

    @router.message(Command("hit"))
    async def hit_cmd(message: types.Message, state: FSMContext):
        state_data = await state.get_data()
        blackjack: Blackjack = state_data.get("blackjack")
        filename, lose = blackjack.hit()

        image = FSInputFile(filename, filename=str(filename))
        if lose:
            await state.clear()
        return await message.reply_photo(image, caption="You busted!" if lose else None)

    @router.message(Command("stand"))
    async def stand_cmd(message: types.Message, state: FSMContext):
        state_data = await state.get_data()
        blackjack: Blackjack = state_data.get("blackjack")
        bet: int = state_data.get("bet")
        filename, result = blackjack.stand()

        image = FSInputFile(filename, filename=str(filename))
        await state.clear()

        if result == 'lose':
            caption = "You lost!"
        elif result == 'draw':
            caption = "It's a draw!"
        else:
            caption = "You won!"
        return await message.reply_photo(image, caption=caption)

    return router
