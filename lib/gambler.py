import asyncio

from aiogram import types


class Gambler:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def convert_dice_val(dice_val: int):
        # bar, plum, lemon, seven
        val = dice_val - 1

        result = ''
        while val > 0:
            result += str(val % 4)
            val //= 4
        return result.ljust(3, '0')

    async def gamble(self, dice_msg: types.Message):
        await asyncio.sleep(1.5)
        result = self.convert_dice_val(dice_msg.dice.value)
        username = dice_msg.from_user.username
        unique = len(set(result))
        if result == '333':
            await dice_msg.reply_animation(
                'https://media1.tenor.com/m/Rpk3q-OLFeYAAAAd/hakari-dance-hakari.gif',
                caption=f"🎉 **BIG JACKPOT!** X5! {username}. {result}"
            )
        elif unique == 1:
            await dice_msg.reply(f"🎉 **JACKPOT!** X2! {username}. {result}")
        elif unique == 2:
            await dice_msg.reply(f"✨ Nice win! X1.2! ✨ {username}. {result}")
        else:
            await dice_msg.reply(f"😢 Better luck next time! {username}. {result}")


gambler = Gambler('')
