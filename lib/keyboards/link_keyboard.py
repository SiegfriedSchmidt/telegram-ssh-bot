from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_link_keyboard(link: str):
    blackjack_keyboard_builder = InlineKeyboardBuilder()
    blackjack_keyboard_builder.button(text="▶️ Open Video", url=link)
    blackjack_keyboard_builder.adjust(1)
    return blackjack_keyboard_builder.as_markup()
