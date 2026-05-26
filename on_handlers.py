import re
from datetime import datetime, timedelta
from collections import Counter
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from database import add_event, get_stats, get_events_for_report, add_reminder, update_last_meltdown_reason, add_user, get_due_reminders, mark_reminder_sent
from keyboards import get_meltdown_keyboard, get_main_keyboard
from utils import format_report, create_report_file, get_random_tip
from config import TIPS

# Состояния для ConversationHandler
WAITING_TIME, WAITING_MESSAGE, WAITING_REASON = range(3)


# === ПРОВЕРКА НАПОМИНАНИЙ ===
async def check_and_send_due_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет и отправляет просроченные напоминания"""
    due_reminders = get_due_reminders()
    for reminder_id, user_id, message in due_reminders:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🔔 *Напоминание!*\n\n{message}",
                parse_mode="Markdown"
            )
            mark_reminder_sent(reminder_id)
            print(f"✅ Reminder {reminder_id} sent to {user_id}")
        except Exception as e:
            print(f"❌ Failed to send reminder {reminder_id}: {e}")


# === НАПОМИНАНИЯ (ДИАЛОГ) ===
async def remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_reminder_dialog'] = True
    await update.message.reply_text("⏰ Введите время в формате ЧЧ:ММ (например, `20:00`)", parse_mode="Markdown")
    return WAITING_TIME

async def remind_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_match = re.match(r'^(\d{1,2}):(\d{2})$', update.message.text)
    if not time_match:
        await update.message.reply_text("❌ Неправильный формат. Используйте ЧЧ:ММ")
        return WAITING_TIME
    hour, minute = int(time_match.group(1)), int(time_match.group(2))
    context.user_data['reminder_hour'] = hour
    context.user_data['reminder_minute'] = minute
    await update.message.reply_text("✏️ Теперь напишите текст напоминания")
    return WAITING_MESSAGE

async def remind_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hour = context.user_data.get('reminder_hour')
    minute = context.user_data.get('reminder_minute')
    text = update.message.text
    now = datetime.now()
    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if reminder_time < now:
        reminder_time += timedelta(days=1)
    
    add_reminder(update.effective_user.id, reminder_time, text)
    
    context.user_data.pop('in_reminder_dialog', None)
    await update.message.reply_text(f"✅ Напоминание установлено на {hour:02d}:{minute:02d}\nТекст: {text}")
    return ConversationHandler.END

async def remind_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('in_reminder_dialog', None)
    await update.message.reply_text("❌ Напоминание отменено")
    return ConversationHandler.END


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
• ⏰ *Напомнить* — установить напоминание

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
