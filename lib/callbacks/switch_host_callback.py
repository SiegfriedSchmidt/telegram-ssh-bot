from aiogram.filters.callback_data import CallbackData


class SwitchHostCallback(CallbackData, prefix="switch"):
    host: str
