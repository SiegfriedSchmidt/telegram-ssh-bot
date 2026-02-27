from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from lib.config_reader import config
from lib.ledger import Ledger
from lib.router_factories import admin_commands, ssh_session, general_commands
from lib.states.confirmation_state import ConfirmationState
from lib.storage import storage
from lib.utils.utils import get_args

router = Router()
router.message.filter(
    F.chat.type.in_(["private"]),
    F.chat.id.in_(config.admin_ids),
    F.from_user.id.in_(config.admin_ids)
)

router.include_routers(
    admin_commands.create_router(),
    general_commands.create_router(),
    ssh_session.create_router()
)


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
        await message.bot.send_message(config.main_group_id, state_message)
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("tx"))
async def tx_cmd(message: types.Message, command: CommandObject, ledger: Ledger):
    args = get_args(command)
    if len(args) < 4 or not args[2].isdecimal():
        return await message.answer('Invalid amount or type of arguments.')

    tx = ledger.record_transaction(*args[:3], " ".join(args[3:]))
    return await message.answer(
        f'Transaction: {tx.from_user} -> {tx.to_user}: {tx.amount}, {tx.description} - recorded!'
    )


@router.message(Command("import_transactions"))
async def import_transactions_cmd(message: types.Message, ledger: Ledger):
    if not message.reply_to_message:
        return await message.answer("You should reply to a message with document.")
    if not message.reply_to_message.document:
        return await message.answer("You should reply to a message containing document.")

    doc = message.reply_to_message.document
    file = await message.bot.get_file(doc.file_id)
    downloaded_file = await message.bot.download_file(file.file_path)
    count = ledger.import_transactions_csv(downloaded_file)
    return await message.answer(f"Total imported transactions: {count}")


@router.message(Command("delete_pending"))
async def delete_pending_cmd(message: types.Message, ledger: Ledger):
    count = ledger.delete_pending_transactions()
    return await message.answer(f"Total deleted pending transactions: {count}")
