import asyncio
from decimal import Decimal
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

    @staticmethod
    async def get_dice_msg(message: types.Message):
        try:
            if message.dice.value:
                dice_msg = message
            else:
                raise AttributeError
        except AttributeError:
            dice_msg = await message.reply_dice(emoji="🎰")

        return dice_msg

    @staticmethod
    async def show_win_message(dice_msg: types.Message, gain_type: GainType, balance_str: str):
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

    def determine_gain_type(self, dice_val: int) -> GainType:
        result = self.convert_dice_val(dice_val)
        unique = len(set(result))
        if result == '333':
            return GainType.big_jackpot
        elif unique == 1:
            return GainType.jackpot
        elif unique == 2:
            return GainType.nice_win
        else:
            return GainType.loss

    @staticmethod
    def determine_gain_amount(gain_type: GainType, bet: Decimal) -> float:
        bet = float(bet)
        match gain_type.value:
            case GainType.big_jackpot:
                return bet * 5
            case GainType.jackpot:
                return bet * 2
            case GainType.nice_win:
                return bet * 1.2
        return 0

    @staticmethod
    def determine_daily_prize(gain_type: GainType):
        match gain_type.value:
            case GainType.big_jackpot:
                return 10000
            case GainType.jackpot:
                return 3000
            case GainType.nice_win:
                return 1000
        return 500

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

        dice_msg = await self.get_dice_msg(message)
        gain_type = self.determine_gain_type(dice_msg.dice.value)
        gain = self.determine_gain_amount(gain_type, bet)
        if gain:
            ledger.record_gain(username, gain, gain_type.value)
        balance_str = f'{username}: {ledger.get_user_balance(username)} coins.'

        await asyncio.sleep(1.5)
        return await self.show_win_message(dice_msg, gain_type, balance_str)

    async def daily_prize(self, message: types.Message):
        dice_msg = await self.get_dice_msg(message)
        username = message.from_user.username
        gain_type = self.determine_gain_type(dice_msg.dice.value)
        gain = self.determine_daily_prize(gain_type)
        ledger.record_gain(username, gain, f'Daily {gain_type.value}')
        balance_str = f'{username}: {ledger.get_user_balance(username)} coins.'
        await asyncio.sleep(1.5)
        return await self.show_win_message(dice_msg, gain_type, balance_str)


gambler = Gambler()
