import asyncio
from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler_tasks import load_active_reminders
from handlers.admin import users_list



async def main():
    # Создаём приложение
    app = Application.builder().token(BOT_TOKEN).build()
    # Подключаем роутер с обработчиками (если он из telegram.ext)
    app.add_handler(router)
    # Регистрируем команду для администратора
    app.add_handler(CommandHandler("users", users_list))
    # Инициализируем базу данных
    init_db()
    print("База данных готова")
    # Загружаем напоминания (если нужны)
    await load_active_reminders(app.bot)
    # Запускаем бота
    print("Бот запущен! 🚀")
    await app.run_polling()
    
if __name__ == "__main__":
    asyncio.run(main())
