from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler, ConversationHandler,
    ContextTypes
)
from handlers.medications import (
    medications_menu,
    add_start, add_name, add_dosage, add_start_date, cancel,
    list_medications,
    NAME, DOSAGE, START_DATE
)
from config import BOT_TOKEN
from database import init_db
from scheduler_tasks import load_active_reminders
from keyboards import get_main_keyboard, get_meltdown_keyboard, get_medications_keyboard

# Импорты из on_handlers
from on_handlers import (
    cmd_start,
    cmd_help,
    track_sleep,
    track_food,
    track_meltdown,
    track_toilet,
    track_mood,
    show_stats,
    export_report,
    random_tip,
    remind_start,
    remind_time,
    remind_message,
    remind_cancel,
    ask_reason_callback,
    save_reason,
    reason_cancel,
    WAITING_TIME,
    WAITING_MESSAGE,
    WAITING_REASON
)

# Импорт админской команды
from handlers.admin import users_list


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок с русским текстом"""
    text = update.message.text
    
    if text == "🌙 Сон":
        await update.message.reply_text("Введите время сна в часах, например: 7.5")
        context.user_data['awaiting'] = 'sleep'
    elif text == "🍎 Еда":
        await update.message.reply_text("Что сегодня ел ребенок?")
        context.user_data['awaiting'] = 'food'
    elif text == "😥 Срыв":
        await update.message.reply_text("Оцените силу от 1 до 5")
        context.user_data['awaiting'] = 'meltdown'
    elif text == "😊 Настроение":
        await update.message.reply_text("Оцените настроение от 1 до 5")
        context.user_data['awaiting'] = 'mood'
    elif text == "📊 Статистика":
        await show_stats(update, context)
    elif text == "💡 Совет":
        await random_tip(update, context)
    elif text == "⏰ Напомнить":
        await remind_start(update, context)
    elif text == "📤 Отчет":
        await export_report(update, context)
    elif text == "💊 Лекарства":
        from handlers.medications import medications_menu
        await medications_menu(update, context)
    elif text == "➕ Добавить лекарство":
        from handlers.medications import add_start
        await add_start(update, context)
    elif text == "📋 Мои лекарства":
        from handlers.medications import list_medications
        await list_medications(update, context)
    elif text == "🔙 Назад в главное меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_keyboard()
        )
    else:
        # Проверяем, есть ли ожидание ввода
        awaiting = context.user_data.get('awaiting')
        if awaiting == 'sleep':
            context.args = [text]
            await track_sleep(update, context)
        elif awaiting == 'food':
            context.args = [text]
            await track_food(update, context)
        elif awaiting == 'meltdown':
            context.args = [text]
            await track_meltdown(update, context)
        elif awaiting == 'mood':
            context.args = [text]
            await track_mood(update, context)
        context.user_data.pop('awaiting', None)


def main():
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # ========== 1. СНАЧАЛА ВСЕ ДИАЛОГИ (ConversationHandler) ==========
    
    # Диалог для напоминаний
    remind_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remind", remind_start)],
        states={
            WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_time)],
            WAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_message)],
        },
        fallbacks=[CommandHandler("cancel", remind_cancel)],
    )
    app.add_handler(remind_conv_handler)

    # Диалог для причин истерик
    reason_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_reason_callback, pattern="add_reason")],
        states={
            WAITING_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reason)],
        },
        fallbacks=[CommandHandler("cancel", reason_cancel)],
    )
    app.add_handler(reason_conv_handler)

    # Диалог добавления лекарства
    med_conv = ConversationHandler(
        entry_points=[
            CommandHandler("med_add", add_start),
            MessageHandler(filters.Regex("^➕ Добавить лекарство$"), add_start)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            DOSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_dosage)],
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_start_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(med_conv)

    # ========== 2. ПОТОМ ВСЕ КОМАНДЫ (CommandHandler) ==========
    
    app.add_handler(CommandHandler("sleep", track_sleep))
    app.add_handler(CommandHandler("food", track_food))
    app.add_handler(CommandHandler("meltdown", track_meltdown))
    app.add_handler(CommandHandler("toilet", track_toilet))
    app.add_handler(CommandHandler("mood", track_mood))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("report", export_report))
    app.add_handler(CommandHandler("tip", random_tip))
    app.add_handler(CommandHandler("remind", remind_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("med", medications_menu))
    app.add_handler(CommandHandler("med_list", list_medications))

    # ========== 3. В САМОМ КОНЦЕ — ОБРАБОТЧИК КНОПОК ==========
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ========== ИНИЦИАЛИЗАЦИЯ ==========
    init_db()
    print("База данных готова")

    # Запуск бота
    print("Бот запущен! 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
