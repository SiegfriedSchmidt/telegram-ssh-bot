from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from lib.config_reader import config
from lib.database import database
from lib.router_factories import commands, ssh_session
from lib.states.confirmation_state import ConfirmationState
from lib.storage import storage
from lib.utils.utils import get_args

router = Router()
router.message.filter(F.chat.type.in_(["private"]), F.chat.id.in_(config.admin_ids))
router.include_routers(commands.create_router(), ssh_session.create_router())


@router.message(Command("notifications"))
async def notifications_cmd(message: types.Message):
    storage.notification_enabled = not storage.notification_enabled
    await message.answer(f'Notifications: {storage.notification_enabled}')


@router.message(Command("send"))
async def send_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.set_state(ConfirmationState.admin_send_confirmation)
    await state.update_data(message=command.args)
    return await message.answer('Do you want to continue (y/n)?')


@router.message(ConfirmationState.admin_send_confirmation)
async def send(message: types.Message, state: FSMContext):
    if message.text == "y":
        state_message = (await state.get_data()).get("message")
        if not state_message:
            return await message.answer('Sorry, message is empty for some reason.')

        await message.answer('sending message...')
        await message.bot.send_message(config.group_id, state_message)
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("set_balance"))
async def set_balance_cmd(message: types.Message, command: CommandObject):
    args = get_args(command)
    if len(args) != 2 or not args[1].isdigit():
        return await message.answer('Sorry, you need to specify a username and balance amount.')

    username = args[0]
    balance = float(args[1])
    database.set_user_balance(database.get_user(username), balance)
    return await message.answer(f'{username} balance is {balance}.')
