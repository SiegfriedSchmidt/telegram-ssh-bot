from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from lib.database import Database
from lib.ssh_manager import SSHManager
from lib.states.ssh_session_state import SSHSessionState

router = Router()
router.message.filter(SSHSessionState.session_activated)


@router.message(Command("deactivate"))
async def deactivate_cmd(message: types.Message, state: FSMContext, database: Database):
    await state.clear()
    return await message.answer('SSH session deactivated!')


@router.message()
async def command(message: types.Message, state: FSMContext):
    ssh_session: SSHManager = (await state.get_data()).get("ssh_session")
    if not ssh_session:
        return await message.answer('No SSH session found!')

    return await message.answer('ssh session working!')
