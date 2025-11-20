from aiogram.fsm.state import StatesGroup, State


class ConfirmationState(StatesGroup):
    update_confirmation = State()
