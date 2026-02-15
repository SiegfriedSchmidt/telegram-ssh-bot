from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from lib.database import Database
from lib.ssh_session import SSHSession
from lib.states.ssh_session_state import SSHSessionState

router = Router()
router.message.filter(SSHSessionState.session_activated)


@router.message(Command("deactivate"))
async def deactivate_cmd(message: types.Message, state: FSMContext, database: Database):
    ssh_session: SSHSession = (await state.get_data()).get("ssh_session")
    ssh_session.close()
    await state.clear()
    return await message.answer('SSH session deactivated!')


@router.message()
async def command(message: types.Message, state: FSMContext):
    ssh_session: SSHSession = (await state.get_data()).get("ssh_session")
    if not ssh_session:
        return await message.answer('No SSH session found!')

    return ssh_session.send_command(message.text)
