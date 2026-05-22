import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler_tasks import scheduler, load_active_reminders
from handlers.admin import users_list



async def main():
    # Инициализация
    app = Application.builder().token(BOT_TOKEN).build()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    # Инициализируем базу данных
    init_db()
    print("База данных готова")

    # Загружаем напоминания
    await load_active_reminders(bot)

    # Запускаем планировщик
   # scheduler.start()

    # Запускаем бота
    print("Бот запущен! 🚀")
    await dp.start_polling(bot)

app.add_handler(CommandHandler("users", users_list))

if __name__ == "__main__":
    asyncio.run(main())
