import asyncio
from aiogram import types

from lib.database import Database, database


class Gambler:
    def __init__(self, db: Database):
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

    async def gamble(self, message: types.Message, bet: float = 0):
        username = message.from_user.username
        user = self.db.get_user(username)
        current_balance = float(user.balance)

        if bet < 0:
            return await message.reply(f"Bet cannot be negative!")

        if bet == 0:
            bet = float(user.bet)
        else:
            self.db.set_user_bet(user, bet)

        if current_balance < bet:
            return await message.reply(f"You don't have enough money: {current_balance}!")
        current_balance -= bet

        try:
            if message.dice.value:
                dice_msg = message
            else:
                raise AttributeError
        except AttributeError:
            dice_msg = await message.reply_dice(emoji="🎰")

        await asyncio.sleep(1.5)
        result = self.convert_dice_val(dice_msg.dice.value)
        unique = len(set(result))
        if result == '333':
            current_balance += 5 * bet
            await dice_msg.reply_animation(
                'https://media1.tenor.com/m/Rpk3q-OLFeYAAAAd/hakari-dance-hakari.gif',
                caption=f"🎉 **BIG JACKPOT!** X5! {username}: {current_balance} coins."
            )
        elif unique == 1:
            current_balance += 2 * bet
            await dice_msg.reply(f"🎉 **JACKPOT!** X2! {username}: {current_balance} coins.")
        elif unique == 2:
            current_balance += 1.2 * bet
            await dice_msg.reply(f"✨ Nice win! X1.2! ✨ {username}: {current_balance} coins.")
        else:
            await dice_msg.reply(f"😢 Better luck next time! {username}: {current_balance} coins.")

        return self.db.set_user_balance(user, current_balance)


gambler = Gambler(database)
