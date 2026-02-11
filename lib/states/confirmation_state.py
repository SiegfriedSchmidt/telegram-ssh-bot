from aiogram.fsm.state import StatesGroup, State


class ConfirmationState(StatesGroup):
    update_confirmation = State()
    reboot_confirmation = State()
    admin_send_confirmation = State()
