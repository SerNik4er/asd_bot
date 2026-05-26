import re
from datetime import datetime, timedelta
from collections import Counter
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from database import add_event, get_stats, get_events_for_report, update_last_meltdown_reason, add_user
from keyboards import get_meltdown_keyboard, get_main_keyboard, get_behavior_keyboard
from utils import format_report, create_report_file, get_random_tip
from config import TIPS

# Состояния для ConversationHandler
WAITING_REASON = 0


# === БАЗОВЫЕ КОМАНДЫ ===
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот, который помогает родителям детей с РАС отслеживать важные события и изменения.

📋 *Что я умею:*
• 🌙 Записывать сон
• 🍎 Записывать еду
• 😥 Отслеживать срывы и их причины
• 😊 Оценивать настроение
• 💊 Вести дневник приёма лекарств
• 📊 Показывать статистику за неделю
• 📤 Готовить отчёт для врача
• 💡 Давать полезные советы

👉 *Как пользоваться:*
Просто нажимай на кнопки внизу экрана — всё интуитивно понятно.

Если что-то непонятно, нажми «❓ Помощь».

Хорошего дня! 🌟
"""
    await update.message.reply_text(
        welcome_text, 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
❓ *Помощь*

*📝 Что умеет этот бот?*
Бот помогает вести дневник наблюдений за ребёнком с РАС. Все данные хранятся локально и никуда не передаются.

*🔘 Основные функции:*

*Отслеживание состояния:*
• 🌙 *Сон* — сколько часов спал ребёнок
• 🍎 *Еда* — что и как ел
• 😥 *Срыв* — сила (1-5) и причина
• 😊 *Настроение* — оценка от 1 до 5

*Аналитика:*
• 📊 *Статистика* — отчёт за последнюю неделю
• 📤 *Отчет* — экспорт данных для врача (за 30 дней)

*Лекарства:*
• 💊 *Лекарства* — добавление, отметка приёма, отчёт по динамике
• Вы можете записывать реакцию, побочные эффекты и улучшения

*Дополнительно:*
• 💡 *Совет* — случайный полезный совет

*🎯 Пример использования:*
1. Нажмите 🌙 *Сон* → введите `7.5` → бот запишет
2. Нажмите 💊 *Лекарства* → ➕ Добавить лекарство → заполните данные
3. Через неделю нажмите 📊 *Статистика* → увидите динамику

*❓ Если что-то не работает:*
• Напишите /start заново
• Убедитесь, что у бота есть доступ к интернету

*💬 Есть вопросы или идеи?*
Напишите разработчику: @ser4ernik

*🔒 Конфиденциальность:*
Все данные хранятся только на вашем устройстве. Бот не передаёт их третьим лицам.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def track_behavior_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога записи поведения"""
    await update.message.reply_text(
        "😔 Выберите тип нежелательного поведения:",
        reply_markup=get_behavior_keyboard()
    )
    return WAITING_BEHAVIOR_TYPE

async def track_behavior_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем тип поведения"""
    if update.message.text == "❌ Отмена":
        await update.message.reply_text("❌ Запись поведения отменена.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    context.user_data['behavior_type'] = update.message.text
    await update.message.reply_text("Оцените силу от 1 до 5 (1 — слабо, 5 — очень сильно):")
    return WAITING_BEHAVIOR_SEVERITY

async def track_behavior_severity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем силу, запрашиваем причину"""
    try:
        severity = max(1, min(5, int(update.message.text)))
        context.user_data['severity'] = severity
    except ValueError:
        await update.message.reply_text("❌ Введите число от 1 до 5")
        return WAITING_BEHAVIOR_SEVERITY
    
    await update.message.reply_text("✏️ Напишите причину (если знаете) или отправьте 'нет'")
    return WAITING_BEHAVIOR_REASON

async def track_behavior_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем причину и завершаем"""
    from database import add_event
    
    reason = update.message.text
    if reason.lower() == "нет":
        reason = ""
    
    add_event(
        user_id=update.effective_user.id,
        event_type="behavior",
        behavior_type=context.user_data.get('behavior_type'),
        value="",
        severity=context.user_data.get('severity'),
        note=reason
    )
    
    behavior_type = context.user_data.get('behavior_type')
    severity = context.user_data.get('severity')
    
    await update.message.reply_text(
        f"✅ Записал поведение:\n"
        f"📋 Тип: {behavior_type}\n"
        f"💪 Сила: {severity}/5\n"
        f"📝 Причина: {reason if reason else 'не указана'}",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END
# === ТРЕКЕРЫ ===
async def track_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите время. Пример: `/sleep 7.5` или `/sleep 23:00-07:00`")
        return
    value = " ".join(args)
    add_event(update.effective_user.id, "sleep", value)
    await update.message.reply_text(f"✅ Записал сон: {value} ч. 🌙")

async def track_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите, что ел ребенок. Пример: `/food гречка, суп`")
        return
    value = " ".join(args)
    add_event(update.effective_user.id, "food", value)
    await update.message.reply_text(f"✅ Записал еду: {value} 🍽️")

async def track_meltdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите силу от 1 до 5. Пример: `/meltdown 4`")
        return
    try:
        severity = max(1, min(5, int(args[0])))
    except ValueError:
        await update.message.reply_text("❌ Сила должна быть числом от 1 до 5")
        return

    add_event(update.effective_user.id, "meltdown", "", severity)
    await update.message.reply_text(
        f"✅ Записал срыв (сила: {severity}/5). Хотите указать причину?",
        reply_markup=get_meltdown_keyboard()
    )

async def track_toilet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите результат. Пример: `/toilet успех` или `/toilet мимо`")
        return
    value = " ".join(args)
    add_event(update.effective_user.id, "toilet", value)
    emoji = "✅🎉" if "успех" in value.lower() else "😔💪"
    await update.message.reply_text(f"Записал туалет: {value} {emoji}")

async def track_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите настроение от 1 до 5. Пример: `/mood 3`")
        return
    try:
        mood = max(1, min(5, int(args[0])))
    except ValueError:
        await update.message.reply_text("❌ Настроение должно быть числом от 1 до 5")
        return

    add_event(update.effective_user.id, "mood", str(mood), mood)
    mood_emoji = {1: "😭", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}
    await update.message.reply_text(f"✅ Записал настроение: {mood_emoji[mood]} ({mood}/5)")


# === СТАТИСТИКА И ОТЧЕТЫ ===
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats(update.effective_user.id)

    text = f"""
📊 **Статистика за неделю**

😭 **Срывы:** {stats['meltdown_count']} раз(а)
📈 **Средняя сила:** {stats['avg_severity']}/5

🌙 **Последние записи сна:**
"""
    for sleep in stats['sleep_records'][:5]:
        text += f"  • {sleep} ч\n"

    if stats['reasons']:
        text += "\n🔍 **Частые причины:**\n"
        for reason, count in Counter(stats['reasons']).most_common(3):
            text += f"  • {reason} ({count} раз)\n"
    else:
        text += "\n💡 *Чтобы видеть причины, указывайте их после срывов*"

    await update.message.reply_text(text, parse_mode="Markdown")

async def export_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_events_for_report(update.effective_user.id, 30)
    if not events:
        await update.message.reply_text("❌ Нет данных за последние 30 дней")
        return

    report_text = format_report(update.effective_user.id, events)
    report_file = create_report_file(report_text)
    await update.message.reply_document(report_file, caption="📄 Отчет для врача")


# === СОВЕТЫ ===
async def random_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tip = get_random_tip(TIPS)
    await update.message.reply_text(tip, parse_mode="Markdown")


# === ОБРАБОТКА ПРИЧИН СРЫВОВ ===
async def ask_reason_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ Напишите причину срыва")
    return WAITING_REASON

async def save_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_last_meltdown_reason(update.effective_user.id, update.message.text)
    await update.message.reply_text(f"✅ Сохранил причину: \"{update.message.text}\"")
    return ConversationHandler.END

async def reason_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Добавление причины отменено")
    return ConversationHandler.END
