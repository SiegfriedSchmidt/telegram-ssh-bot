from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from lib.config_reader import config
from lib.ssh_interactive_session import SSHInteractiveSession
from lib.states.ssh_session_state import SSHSessionState

router = Router()
router.message.filter(F.from_user.id.in_(config.admin_ids))
router.message.filter(SSHSessionState.session_activated)


@router.message(Command("deactivate"))
async def deactivate_cmd(message: types.Message, state: FSMContext):
    ssh_session: SSHInteractiveSession = (await state.get_data()).get("ssh_session")
    ssh_session.close()
    await state.clear()
    return await message.answer('SSH session deactivated!')


@router.message()
async def command(message: types.Message, state: FSMContext):
    ssh_session: SSHInteractiveSession = (await state.get_data()).get("ssh_session")
    if not ssh_session:
        return await message.answer('No SSH session found!')

    return ssh_session.send_command(message.text)
