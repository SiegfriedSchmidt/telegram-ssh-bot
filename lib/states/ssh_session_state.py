from aiogram.fsm.state import StatesGroup, State


class SSHSessionState(StatesGroup):
    session_activated = State()
