from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database import add_medication, get_active_medications, log_medication_take

# Состояния для диалога добавления лекарства
NAME, DOSAGE, START_DATE = range(3)
TAKE_SELECT, TAKE_REACTION, TAKE_SIDE_EFFECTS, TAKE_IMPROVEMENTS = range(4, 8)

async def medications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню лекарств (вызывается по кнопке)"""
    from keyboards import get_medications_keyboard
    
    text = (
        "💊 *Управление лекарствами*\n\n"
        "Здесь вы можете:\n"
        "• Добавить новое лекарство\n"
        "• Посмотреть список активных препаратов\n"
        "• Отметить приём\n"
        "• Сформировать отчёт для врача"
    )
    await update.message.reply_text(
        text, 
        parse_mode="Markdown",
        reply_markup=get_medications_keyboard()
    )

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога добавления лекарства"""
    await update.message.reply_text("Введите название лекарства:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"DEBUG: add_name вызвана, текст={update.message.text}")
    context.user_data['med_name'] = update.message.text
    await update.message.reply_text("Введите дозировку (например, 0.5 мг):")
    print("DEBUG: возвращаем DOSAGE")
    return DOSAGE

async def add_dosage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['med_dosage'] = update.message.text
    await update.message.reply_text("Введите дату начала приёма (ДД.ММ.ГГГГ):")
    return START_DATE

def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы для Telegram Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def add_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date = update.message.text
    user_id = update.effective_user.id
    name = context.user_data['med_name']
    dosage = context.user_data['med_dosage']
    
    # Экранируем спецсимволы
    name_escaped = escape_markdown(name)
    dosage_escaped = escape_markdown(dosage)
    date_escaped = escape_markdown(start_date)
    
    med_id = add_medication(user_id, name, dosage, start_date)
    
    await update.message.reply_text(
        f"✅ Лекарство *{name_escaped}* ({dosage_escaped}) добавлено!\n"
        f"📅 Дата начала: {date_escaped}\n\n"
        f"Теперь вы можете отмечать приёмы в меню лекарств.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Добавление лекарства отменено.")
    return ConversationHandler.END

async def list_medications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список активных лекарств"""
    user_id = update.effective_user.id
    meds = get_active_medications(user_id)
    
    if not meds:
        await update.message.reply_text("💊 У вас пока нет добавленных лекарств.\nДобавьте командой /med_add")
        return
    
    text = "💊 *Ваши лекарства:*\n\n"
    for med in meds:
        med_id, name, dosage, start_date = med
        text += f"• *{name}* ({dosage})\n   с {start_date}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database import get_active_medications, log_medication_take

async def take_medication_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога отметки приёма: показать список активных лекарств"""
    user_id = update.effective_user.id
    meds = get_active_medications(user_id)
    
    if not meds:
        await update.message.reply_text("💊 У вас пока нет активных лекарств. Сначала добавьте их через '➕ Добавить лекарство'.")
        return ConversationHandler.END
    
    # Отправляем список лекарств с кнопками выбора
    keyboard = []
    for med in meds:
        med_id, name, dosage, start_date = med
        keyboard.append([InlineKeyboardButton(f"{name} ({dosage})", callback_data=f"take_{med_id}")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_take")])
    
    await update.message.reply_text(
        "💊 Выберите лекарство, которое дали ребёнку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TAKE_SELECT

async def take_medication_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал лекарство"""
    query = update.callback_query
    await query.answer()
    
    med_id = int(query.data.split("_")[1])
    context.user_data['take_med_id'] = med_id
    
    # Получаем название лекарства для сохранения в контексте (опционально)
    meds = get_active_medications(query.from_user.id)
    for med in meds:
        if med[0] == med_id:
            context.user_data['take_med_name'] = med[1]
            break
    
    await query.message.reply_text(
        "📝 Как ребёнок перенёс приём?\n"
        "Выберите вариант или напишите свой:",
        reply_markup=ReplyKeyboardMarkup([
            ["👍 Хорошо", "😐 Нормально"],
            ["⚠️ Была побочка", "😟 Плохо"],
            ["❌ Отмена"]
        ], resize_keyboard=True)
    )
    return TAKE_REACTION

async def take_medication_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем реакцию, спрашиваем о побочках"""
    context.user_data['take_reaction'] = update.message.text
    
    await update.message.reply_text(
        "⚠️ Были ли побочные эффекты?\n"
        "Если да, опишите какие. Если нет, напишите 'нет'.",
        reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
    )
    return TAKE_SIDE_EFFECTS

async def take_medication_side_effects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем побочки, спрашиваем об улучшениях"""
    context.user_data['take_side_effects'] = update.message.text
    
    await update.message.reply_text(
        "📈 Что улучшилось после приёма?\n"
        "Выберите или напишите своё:",
        reply_markup=ReplyKeyboardMarkup([
            ["🌙 Сон", "🍎 Аппетит", "😌 Поведение"],
            ["📖 Внимание", "😊 Настроение", "Ничего"],
            ["❌ Отмена"]
        ], resize_keyboard=True)
    )
    return TAKE_IMPROVEMENTS

async def take_medication_improvements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем все данные в БД и завершаем"""
    user_id = update.effective_user.id
    med_id = context.user_data.get('take_med_id')
    med_name = context.user_data.get('take_med_name', 'лекарства')
    reaction = context.user_data.get('take_reaction')
    side_effects = context.user_data.get('take_side_effects')
    improvements = update.message.text
    
    # Сохраняем в БД
    log_medication_take(med_id, reaction, side_effects, improvements)
    
    from keyboards import get_main_keyboard
    await update.message.reply_text(
        f"✅ Приём {med_name} записан!\n\n"
        f"📝 Реакция: {reaction}\n"
        f"⚠️ Побочные эффекты: {side_effects}\n"
        f"📈 Улучшения: {improvements}",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена отметки приёма"""
    from keyboards import get_main_keyboard
    await update.message.reply_text("❌ Отметка приёма отменена.", reply_markup=get_main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END
