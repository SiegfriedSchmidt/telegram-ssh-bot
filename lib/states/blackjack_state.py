from aiogram.fsm.state import StatesGroup, State


class BlackjackState(StatesGroup):
    blackjack_activated = State()
