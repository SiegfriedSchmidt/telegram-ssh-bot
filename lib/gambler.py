import asyncio
from decimal import Decimal
from typing import Tuple

from aiogram import types
from lib.ledger import ledger
from lib import database
from lib.models import GainType


class Gambler:
    @staticmethod
    def convert_dice_val(dice_val: int):
        # bar, plum, lemon, seven
        val = dice_val - 1

        result = ''
        while val > 0:
            result += str(val % 4)
            val //= 4
        return result.ljust(3, '0')

    def determine_gain(self, dice_val: int, bet: Decimal) -> Tuple[GainType, float]:
        bet = float(bet)
        result = self.convert_dice_val(dice_val)
        unique = len(set(result))
        if result == '333':
            gain_type = GainType.big_jackpot
            gain = bet * 5
        elif unique == 1:
            gain_type = GainType.jackpot
            gain = bet * 2
        elif unique == 2:
            gain_type = GainType.nice_win
            gain = bet * 1.2
        else:
            gain_type = GainType.loss
            gain = 0
        return gain_type, gain

    async def gamble(self, message: types.Message, bet: Decimal | str | float = 0):
        bet = Decimal(bet)
        username = message.from_user.username

        if bet < 0:
            return await message.reply(f"Bet cannot be negative!")

        if bet == 0:
            bet = database.get_user_bet(username)
        else:
            database.set_user_bet(username, bet)

        try:
            ledger.record_deposit(username, bet, "bet")
        except ValueError:
            return await message.reply(f"You don't have enough money: {ledger.get_user_balance(username)} < {bet}!")

        try:
            if message.dice.value:
                dice_msg = message
            else:
                raise AttributeError
        except AttributeError:
            dice_msg = await message.reply_dice(emoji="🎰")

        gain_type, gain = self.determine_gain(dice_msg.dice.value, bet)
        if gain:
            ledger.record_gain(username, gain, gain_type.value)
        balance_str = f'{username}: {ledger.get_user_balance(username)} coins.'

        await asyncio.sleep(1.5)
        match gain_type.value:
            case GainType.big_jackpot:
                await dice_msg.reply_animation(
                    'https://media1.tenor.com/m/Rpk3q-OLFeYAAAAd/hakari-dance-hakari.gif',
                    caption=f"🎉 **BIG JACKPOT!** X5! {balance_str}"
                )
            case GainType.jackpot:
                await dice_msg.reply(f"🎉 **JACKPOT!** X2! {balance_str}")
            case GainType.nice_win:
                await dice_msg.reply(f"✨ Nice win! X1.2! ✨ {balance_str}")
            case GainType.loss:
                await dice_msg.reply(f"😢 Better luck next time, loser! {balance_str}")

        return None


gambler = Gambler()
