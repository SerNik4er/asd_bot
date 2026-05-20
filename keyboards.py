from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_meltdown_keyboard():
    """Клавиатура после записи истерики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardMarkup(text="👍 Указать причину", calback_data="add_reason")]
    ])

def get_main_keyboard():
    """Основная клавиатура для быстрых команд"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/сон"), KeyboardButton(text="/еда")],
            [KeyboardButton(text="/истерика"), KeyboardButton(text="/настроение")],
            [KeyboardButton(text="/статистика"), KeyboardButton(text="/совет")]
        ],
        resize_keyboard=True
    )