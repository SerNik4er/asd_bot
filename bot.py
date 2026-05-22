import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler_tasks import scheduler, load_active_reminders


async def main():
    # Инициализация
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    # Инициализируем базу данных
    init_db()
    print("База данных готова")

    # Загружаем напоминания
    await load_active_reminders(bot)

    # Запускаем планировщик
    scheduler.start()

    # Запускаем бота
    print("Бот запущен! 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
