from aiogram.fsm.state import StatesGroup, State


class SwitchState(StatesGroup):
    switching = State()
