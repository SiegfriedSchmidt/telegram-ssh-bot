from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from lib.config_reader import config
from lib.database import Database
from lib.states.confirmation_state import ConfirmationState
from lib.storage import storage
from lib.utils.utils import get_args

router = Router()
router.message.filter(F.chat.type.in_(["private"]), F.chat.id == int(config.admin_id.get_secret_value()))


@router.message(Command("h"))
async def h_cmd(message: types.Message, state: FSMContext):
    await message.answer('Hello there!')


@router.message(Command("notifications"))
async def notifications_cmd(message: types.Message, state: FSMContext):
    storage.notification_enabled = not storage.notification_enabled
    await message.answer(f'Notifications: {storage.notification_enabled}')


@router.message(Command("update"))
async def update_cmd(message: types.Message, database: Database, state: FSMContext):
    await message.answer('performing image update...')
    database.ssh_manager.update()


@router.message(Command("send"))
async def send_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.set_state(ConfirmationState.admin_send_confirmation)
    await state.update_data(message=command.args)
    return await message.answer('Do you want to continue (y/n)?')


@router.message(ConfirmationState.admin_send_confirmation)
async def send(message: types.Message, database: Database, state: FSMContext):
    if message.text == "y":
        state_message = (await state.get_data()).get("message")
        if not state_message:
            return await message.answer('Sorry, message is empty for some reason.')

        await message.answer('sending message...')
        await message.bot.send_message(int(config.group_id.get_secret_value()), state_message)
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("openconnect"))
async def openconnect_cmd(message: types.Message, command: CommandObject, database: Database):
    args = get_args(command)
    if len(args) == 0 or len(args) > 1 or args[0] not in ['status', 'restart', 'stop', 'start']:
        return await message.answer('invalid syntax, openconnect status|restart|stop|start')

    result, error = database.ssh_manager.openconnect(command.args)
    if not result:
        return await message.answer(error)
    return await message.answer(result)
