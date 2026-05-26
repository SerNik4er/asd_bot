from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard():
    """Главная клавиатура с текстовыми кнопками (без /)"""
    buttons = [
        [KeyboardButton("🌙 Сон"), KeyboardButton("🍎 Еда")],
        [KeyboardButton("😥 Срыв"), KeyboardButton("😊 Настроение")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("💊 Лекарства")],
        [KeyboardButton("📤 Отчет")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("💡 Совет")]
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
