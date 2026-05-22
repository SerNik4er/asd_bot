from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from config import BOT_TOKEN
from database import init_db
from scheduler_tasks import load_active_reminders

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
    text = update.message.text
    
    if text == "🌙 Сон":
        await update.message.reply_text("Введите время сна в часах, например: 7.5")
        context.user_data['awaiting'] = 'sleep'
    elif text == "🍎 Еда":
        await update.message.reply_text("Что сегодня ел ребенок?")
        context.user_data['awaiting'] = 'food'
    elif text == "😭 Истерика":
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


def main():
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # === ОБЫЧНЫЕ КОМАНДЫ ===
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("sleep", track_sleep))
    app.add_handler(CommandHandler("food", track_food))
    app.add_handler(CommandHandler("meltdown", track_meltdown))
    app.add_handler(CommandHandler("toilet", track_toilet))
    app.add_handler(CommandHandler("mood", track_mood))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("report", export_report))
    app.add_handler(CommandHandler("tip", random_tip))
    app.add_handler(CommandHandler("сон", track_sleep))
    app.add_handler(CommandHandler("еда", track_food))
    app.add_handler(CommandHandler("истерика", track_meltdown))
    app.add_handler(CommandHandler("туалет", track_toilet))
    app.add_handler(CommandHandler("настроение", track_mood))
    app.add_handler(CommandHandler("статистика", show_stats))
    app.add_handler(CommandHandler("отчет", export_report))
    app.add_handler(CommandHandler("совет", random_tip))
    app.add_handler(CommandHandler("напомнить", remind_start))
    app.add_handler(CommandHandler("помощь", cmd_help))
    app.add_handler(CommandHandler("старт", cmd_start))
    app.add_handler(CommandHandler("пользователи", users_list))

    # === АДМИНСКАЯ КОМАНДА ===
    app.add_handler(CommandHandler("users", users_list))

    # === ДИАЛОГ ДЛЯ НАПОМИНАНИЙ (ConversationHandler) ===
    remind_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remind", remind_start)],
        states={
            WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_time)],
            WAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_message)],
        },
        fallbacks=[CommandHandler("cancel", remind_cancel)],
    )
    app.add_handler(remind_conv_handler)

    # === ДИАЛОГ ДЛЯ ПРИЧИН ИСТЕРИК (по кнопке) ===
    reason_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_reason_callback, pattern="add_reason")],
        states={
            WAITING_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reason)],
        },
        fallbacks=[CommandHandler("cancel", reason_cancel)],
    )
    app.add_handler(reason_conv_handler)

    # === ИНИЦИАЛИЗАЦИЯ ===
    init_db()
    print("База данных готова")

    # Запускаем бота (без asyncio.run)
    print("Бот запущен! 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
