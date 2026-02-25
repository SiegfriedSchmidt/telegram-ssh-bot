import asyncio
from decimal import Decimal
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.utils.chat_action import ChatActionMiddleware
from lib import database
from lib.bot_commands import text_bot_general_commands, text_bot_admin_commands
from lib.config_reader import config
from lib.ledger import ledger
from lib.api.gemini_api import gemini_api
from lib.api.joke_api import get_joke
from lib.api.meme_api import get_meme
from lib.api.geoip_api import geoip
from lib.gambler import gambler
from lib.utils.utils import get_args, large_respond


def create_router():
    router = Router()
    router.message.middleware(ChatActionMiddleware())

    @router.message(Command("h"))
    async def h_cmd(message: types.Message):
        if message.from_user.id in config.admin_ids:
            await message.answer(text_bot_admin_commands)
        else:
            await message.answer(text_bot_general_commands)

    @router.message(Command("joke"))
    async def joke_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            joke_type = args[0] if len(args) == 1 else None
            joke = await get_joke(joke_type)
        except Exception as e:
            return await message.answer(str(e))
        return await message.answer(joke)

    @router.message(Command("meme"))
    async def meme_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            meme_subreddit = args[0] if len(args) == 1 else None
            url, caption = await get_meme(meme_subreddit)
        except Exception as e:
            return await message.answer(str(e))

        try:
            if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                await message.answer_photo(url, caption=caption)
            elif url.endswith('.gif'):
                await message.answer_animation(url, caption=caption)
            elif url.endswith(('.mp4', '.gifv', '.webm')):
                await message.answer_video(url, caption=caption)
        except TelegramBadRequest:
            await asyncio.sleep(1)
            await message.answer(f"{url}\n\n{caption}", disable_web_page_preview=False)

        return None

    @router.message(Command("ask"))
    async def ask_cmd(message: types.Message, command: CommandObject):
        args = command.args
        if not args:
            return await message.answer("You need to specify a query.")

        answer = await message.answer('asking...')
        response = await gemini_api.ask(args)
        await large_respond(message, response)
        return await answer.delete()

    @router.message(Command("geoip"))
    async def geoip_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) == 0:
            return await message.answer('too few args!')

        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            json = await geoip(args[0])
            text = '\n'.join(f"{key}: {val}" for key, val in json.items())
        except Exception as e:
            return await message.answer(str(e))
        return await message.answer(text)

    @router.message(Command("niggachain"))
    async def chain_cmd(message: types.Message):
        return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')

    @router.message(Command("gamble"))
    async def gamble_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        bet = 0
        if len(args) == 1:
            if not args[0].isdecimal() or (bet := Decimal(args[0])) < 0:
                return await message.answer('bet should be decimal and be greater than 0!')

        if len(args) > 1:
            return await message.answer('too many args!')

        return await gambler.gamble(message, bet)

    @router.message(Command("galton"))
    async def galton_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        bet = 0
        attempts = 1
        if len(args) >= 1:
            if not args[0].isdecimal() or (bet := Decimal(args[0])) < 0:
                return await message.answer('bet should be decimal and be greater than 0!')

        if len(args) == 2:
            if not args[1].isdigit() or (attempts := int(args[1])) < 1:
                return await message.answer('number of attempts should be decimal and be greater than 0!')

        if len(args) > 2:
            return await message.answer('too many args!')

        return await gambler.galton(message, bet, attempts)

    @router.message(Command("balance"))
    async def balance_cmd(message: types.Message):
        return await message.answer(f"Your balance is {ledger.get_user_balance(message.from_user.username)}.")

    @router.message(Command("transfer"))
    async def transfer_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if message.reply_to_message:
            to_user = message.reply_to_message.from_user.username
            if len(args) == 1 and args[0].isdecimal():
                amount = args[0]
            else:
                return await message.answer('Correct amount is required!')
        elif len(args) == 2 and args[0].isdecimal():
            amount = args[0]
            to_user = args[1]
        else:
            return await message.answer('Invalid syntax!')
        from_user = message.from_user.username
        ledger.record_transaction(from_user, to_user, amount, "transfer")
        return await message.answer(f"Successfully transferred {amount} to {to_user}!")

    @router.message(Command("daily_prize"))
    async def daily_prize_cmd(message: types.Message):
        if database.available_daily_prize(message.from_user.username):
            return await gambler.daily_prize(message)
        else:
            return await message.answer('Your daily prize already obtained! Wait for the next day!')

    @router.message(Command("ledger"))
    async def ledger_cmd(message: types.Message):
        txs = ledger.get_recent_transactions(limit=100)
        txs_count = ledger.get_transactions_count()
        text_txs = '\n'.join([
            f'{tx.height}. {tx.from_user} -> {tx.to_user}, {tx.amount}, {tx.description}' for tx in txs
        ])
        return await message.answer(f"<b>Ledger ({txs_count} transactions):</b>\n{text_txs}", parse_mode='html')

    @router.message(Command("leaderboard"))
    async def leaderboard_cmd(message: types.Message):
        balances = ledger.get_all_balances()[1:]
        text = '\n'.join([
            f'{idx + 1}. {username}: {amount}' for idx, (username, amount) in enumerate(balances)
        ])
        return await message.answer(f"<b>Leaderboard:</b>\n{text}", parse_mode='html')

    return router
