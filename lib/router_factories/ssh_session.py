from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from lib.ssh_interactive_session import SSHInteractiveSession
from lib.states.ssh_session_state import SSHSessionState


def create_router():
    router = Router()
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

    return router
