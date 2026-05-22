from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_meltdown_keyboard():
    """Клавиатура для выбора причины истерики"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить причину", callback_data="add_reason")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard():
    """Главная клавиатура с кнопками-командами"""
    buttons = [
        [KeyboardButton("/sleep"), KeyboardButton("/food")],
        [KeyboardButton("/meltdown"), KeyboardButton("/mood")],
        [KeyboardButton("/stats"), KeyboardButton("/tip")],
        [KeyboardButton("/remind"), KeyboardButton("/report")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [[KeyboardButton("/cancel")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
