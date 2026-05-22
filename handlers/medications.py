from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import add_medication, get_active_medications

# Состояния для диалога добавления лекарства
NAME, DOSAGE, START_DATE = range(3)

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

async def add_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date = update.message.text
    user_id = update.effective_user.id
    name = context.user_data['med_name']
    dosage = context.user_data['med_dosage']
    
    med_id = add_medication(user_id, name, dosage, start_date)
    
    await update.message.reply_text(
        f"✅ Лекарство *{name}* ({dosage}) добавлено!\n"
        f"📅 Дата начала: {start_date}\n\n"
        f"Теперь вы можете отмечать приёмы командой /med_take",
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
