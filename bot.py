from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler, ConversationHandler,
    ContextTypes
)
from handlers.medications import (
    medications_menu,
    add_start, add_name, add_dosage, add_start_date, cancel,
    list_medications, take_medication_start, take_medication_selected,
    take_medication_reaction, take_medication_side_effects,
    take_medication_improvements, cancel_take,
    NAME, DOSAGE, START_DATE, TAKE_SELECT, TAKE_REACTION, TAKE_SIDE_EFFECTS, TAKE_IMPROVEMENTS, REPORT_SELECT
)
from config import BOT_TOKEN
from database import init_db
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
    print(f"DEBUG: handle_text получил текст: '{text}'")

    if context.user_data.get('in_reminder_dialog'):
        print("DEBUG: В диалоге напоминания, пропускаем")
        return
    elif text == "🌙 Сон":
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
    elif text == "📊 Отчёт по лекарствам":
        from handlers.medications import report_medication_start
        await report_medication_start(update, context)
    elif text == "❓ Помощь":
        await cmd_help(update, context)
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


async def force_init_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import init_db
    init_db()
    await update.message.reply_text("✅ База данных инициализирована (все таблицы созданы)")

async def check_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import get_connection
    import os
    
    # Проверяем путь к БД
    from config import DATABASE_NAME
    await update.message.reply_text(f"📁 Путь к БД: {DATABASE_NAME}")
    
    # Проверяем, существует ли файл
    if os.path.exists(DATABASE_NAME):
        await update.message.reply_text(f"✅ Файл БД существует, размер: {os.path.getsize(DATABASE_NAME)} байт")
    else:
        await update.message.reply_text("❌ Файл БД НЕ существует")
    
    # Проверяем таблицы
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            table_list = ", ".join([t[0] for t in tables])
            await update.message.reply_text(f"📋 Таблицы в БД: {table_list}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# В main():
def main():
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # ========== ДИАГНОСТИЧЕСКИЕ КОМАНДЫ ==========
    app.add_handler(CommandHandler("initdb", force_init_db))
    app.add_handler(CommandHandler("checkdb", check_db))

    # ========== 1. СНАЧАЛА ВСЕ ДИАЛОГИ (ConversationHandler) ==========
    
    # Диалог для напоминаний
    remind_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("remind", remind_start),
        MessageHandler(filters.Regex("^⏰ Напомнить$"), remind_start)
    ],
    states={
        WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_time)],
        WAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_message)],
    },
    fallbacks=[CommandHandler("cancel", remind_cancel)],
)
app.add_handler(remind_conv_handler)
    
    # Диалог отчёта по лекарству
from handlers.medications import (
    report_medication_start, report_medication_selected, cancel_report,
    REPORT_SELECT
    )

    report_conv = ConversationHandler(
        entry_points=[
            CommandHandler("med_report", report_medication_start),
            MessageHandler(filters.Regex("^📊 Отчёт по лекарствам$"), report_medication_start)
        ],
        states={
            REPORT_SELECT: [CallbackQueryHandler(report_medication_selected, pattern="^report_")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_report),
            CallbackQueryHandler(cancel_report, pattern="^cancel_report$"),
        ],
    )
    app.add_handler(report_conv)
    
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

    # Диалог для отметки приёма
    take_med_conv = ConversationHandler(
        entry_points=[
            CommandHandler("med_take", take_medication_start),
            MessageHandler(filters.Regex("^💊 Отметить приём$"), take_medication_start)
        ],
        states={
            TAKE_SELECT: [CallbackQueryHandler(take_medication_selected, pattern="^take_")],
            TAKE_REACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_medication_reaction)],
            TAKE_SIDE_EFFECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_medication_side_effects)],
            TAKE_IMPROVEMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_medication_improvements)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_take),
            CallbackQueryHandler(cancel_take, pattern="^cancel_take$"),
        ],
    )
    app.add_handler(take_med_conv)

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

    # ========== ЗАПУСК ПЛАНИРОВЩИКА ==========
    start_scheduler()
    print("Планировщик запущен")

    # ========== ЗАПУСК БОТА ==========
    print("Бот запущен! 🚀")
    app.run_polling()

    # ========== ОСТАНОВКА ПЛАНИРОВЩИКА ПРИ ЗАВЕРШЕНИИ ==========
    stop_scheduler()


if __name__ == "__main__":
    main()
