import re
from datetime import datetime, timedelta
from collections import Counter
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # ← Добавить эту строку

from database import add_event, get_stats, get_events_for_report, add_reminder, update_last_meltdown_reason
from keyboards import get_meltdown_keyboard, get_main_keyboard
from utils import format_report, create_report_file, get_random_tip
from scheduler_tasks import schedule_reminder
from config import TIPS

# ===== СОСТОЯНИЯ (добавить прямо сюда) =====
class ReminderState(StatesGroup):
    waiting_for_time = State()
    waiting_for_message = State()

class ReasonState(StatesGroup):
    waiting_for_reason = State()

router = Router()


# === БАЗОВЫЕ КОМАНДЫ ===
@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = """
👋 Привет! Я помощник для родителей детей с РАС.

📝 **Основные команды:**
🌙 `/сон 7.5` - записать сон
🍎 `/еда гречка` - записать еду
😭 `/истерика 4` - записать истерику
😊 `/настроение 3` - записать настроение
📊 `/статистика` - отчет за неделю
💡 `/совет` - совет дня
⏰ `/напомнить` - установить напоминание
📤 `/отчет` - экспорт для врача
"""
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# === ТРЕКЕРЫ ===
@router.message(Command("сон"))
async def track_sleep(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите время. Пример: `/сон 7.5` или `/сон 23:00-07:00`")
        return
    add_event(message.from_user.id, "sleep", args[1])
    await message.answer(f"✅ Записал сон: {args[1]} ч. 🌙")


@router.message(Command("еда"))
async def track_food(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите, что ел ребенок. Пример: `/еда гречка, суп`")
        return
    add_event(message.from_user.id, "food", args[1])
    await message.answer(f"✅ Записал еду: {args[1]} 🍽️")


@router.message(Command("истерика"))
async def track_meltdown(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите силу от 1 до 5. Пример: `/истерика 4`")
        return
    try:
        severity = max(1, min(5, int(args[1])))
    except ValueError:
        await message.answer("❌ Сила должна быть числом от 1 до 5")
        return

    add_event(message.from_user.id, "meltdown", "", severity)
    await message.answer(f"✅ Записал истерику (сила: {severity}/5). Хотите указать причину?",
                         reply_markup=get_meltdown_keyboard())


@router.message(Command("туалет"))
async def track_toilet(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите результат. Пример: `/туалет успех` или `/туалет мимо`")
        return
    add_event(message.from_user.id, "toilet", args[1])
    emoji = "✅🎉" if "успех" in args[1].lower() else "😔💪"
    await message.answer(f"Записал туалет: {args[1]} {emoji}")


@router.message(Command("настроение"))
async def track_mood(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите настроение от 1 до 5. Пример: `/настроение 3`")
        return
    try:
        mood = max(1, min(5, int(args[1])))
    except ValueError:
        await message.answer("❌ Настроение должно быть числом от 1 до 5")
        return

    add_event(message.from_user.id, "mood", str(mood), mood)
    mood_emoji = {1: "😭", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}
    await message.answer(f"✅ Записал настроение: {mood_emoji[mood]} ({mood}/5)")


# === СТАТИСТИКА И ОТЧЕТЫ ===
@router.message(Command("статистика"))
async def show_stats(message: Message):
    stats = get_stats(message.from_user.id)

    text = f"""
📊 **Статистика за неделю**

😭 **Истерики:** {stats['meltdown_count']} раз(а)
📈 **Средняя сила:** {stats['avg_severity']}/5

🌙 **Последние записи сна:**
"""
    for sleep in stats['sleep_records'][:5]:
        text += f"  • {sleep} ч\n"

    if stats['reasons']:
        from collections import Counter
        text += "\n🔍 **Частые причины:**\n"
        for reason, count in Counter(stats['reasons']).most_common(3):
            text += f"  • {reason} ({count} раз)\n"
    else:
        text += "\n💡 *Чтобы видеть причины, указывайте их после истерик*"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("отчет"))
async def export_report(message: Message):
    events = get_events_for_report(message.from_user.id, 30)
    if not events:
        await message.answer("❌ Нет данных за последние 30 дней")
        return

    report_text = format_report(message.from_user.id, events)
    report_file = create_report_file(report_text)
    await message.answer_document(report_file, caption="📄 Отчет для врача")


# === СОВЕТЫ ===
@router.message(Command("совет"))
async def random_tip(message: Message):
    tip = get_random_tip(TIPS)
    await message.answer(tip, parse_mode="Markdown")


# === НАПОМИНАНИЯ ===
@router.message(Command("напомнить"))
async def set_reminder(message: Message, state: FSMContext):
    await message.answer("⏰ Введите время в формате ЧЧ:ММ (например, `20:00`)", parse_mode="Markdown")
    await state.set_state(ReminderState.waiting_for_time)


@router.message(ReminderState.waiting_for_time)
async def reminder_time(message: Message, state: FSMContext):
    time_match = re.match(r'^(\d{1,2}):(\d{2})$', message.text)
    if not time_match:
        await message.answer("❌ Неправильный формат. Используйте ЧЧ:ММ")
        return

    hour, minute = int(time_match.group(1)), int(time_match.group(2))
    await state.update_data(hour=hour, minute=minute)
    await message.answer("✏️ Теперь напишите текст напоминания")
    await state.set_state(ReminderState.waiting_for_message)


@router.message(ReminderState.waiting_for_message)
async def reminder_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    hour, minute = data['hour'], data['minute']

    now = datetime.now()
    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if reminder_time < now:
        reminder_time += timedelta(days=1)

    reminder_id = add_reminder(message.from_user.id, reminder_time, message.text)
    schedule_reminder(bot, message.from_user.id, reminder_time, message.text, reminder_id)

    await message.answer(f"✅ Напоминание установлено на {hour:02d}:{minute:02d}\nТекст: {message.text}")
    await state.clear()


# === ОБРАБОТКА ПРИЧИН ИСТЕРИК ===
@router.callback_query(F.data == "add_reason")
async def ask_reason(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Напишите причину истерики")
    await state.set_state(ReasonState.waiting_for_reason)
    await callback.answer()


@router.message(ReasonState.waiting_for_reason)
async def save_reason(message: Message, state: FSMContext):
    update_last_meltdown_reason(message.from_user.id, message.text)
    await message.answer(f"✅ Сохранил причину: \"{message.text}\"")
    await state.clear()


# === ПОМОЩЬ ===
@router.message(Command("help"))
async def cmd_help(message: Message):
    await cmd_start(message)
