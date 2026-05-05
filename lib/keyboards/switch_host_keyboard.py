from lib.callbacks.switch_host_callback import SwitchHostCallback
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_switch_host_keyboard(hosts: list[str]):
    switch_host_keyboard_builder = InlineKeyboardBuilder()

    for host in hosts:
        switch_host_keyboard_builder.button(
            text=host,
            callback_data=SwitchHostCallback(host=host)
        )

    switch_host_keyboard_builder.adjust(len(hosts))
    return switch_host_keyboard_builder.as_markup()
