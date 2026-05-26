from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard():
    """Главная клавиатура с текстовыми кнопками (без /)"""
    buttons = [
        [KeyboardButton("🌙 Сон"), KeyboardButton("🍎 Еда")],
        [KeyboardButton("😔 Поведение"), KeyboardButton("😊 Настроение")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("💊 Лекарства")],
        [KeyboardButton("📤 Отчет"), KeyboardButton("💡 Совет")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
def get_behavior_keyboard():
    """Клавиатура для выбора типа нежелательного поведения"""
    buttons = [
        [KeyboardButton("🔄 Стимминг"), KeyboardButton("🙈 Нет контакта")],
        [KeyboardButton("📉 Падение на пол"), KeyboardButton("🏃 Побег")],
        [KeyboardButton("🪜 Лазание"), KeyboardButton("📢 Крики")],
        [KeyboardButton("😭 Плач"), KeyboardButton("💥 Разрушение")],
        [KeyboardButton("👊 Агрессия"), KeyboardButton("🤕 Самоагрессия")],
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_medications_keyboard():
    """Клавиатура меню управления лекарствами"""
    buttons = [
        [KeyboardButton("➕ Добавить лекарство")],
        [KeyboardButton("📋 Мои лекарства")],
        [KeyboardButton("💊 Отметить приём")],
        [KeyboardButton("📊 Отчёт по лекарствам")],
        [KeyboardButton("🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_meltdown_keyboard():
    """Клавиатура для выбора причины истерики"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить причину", callback_data="add_reason")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [[KeyboardButton("❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
