from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_switch_host_keyboard(hosts: list[str]):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=host) for host in hosts]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True
    )
