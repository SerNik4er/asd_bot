import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_NAME = os.getenv("DATABASE_NAME", "autism_helper.db")
if not BOT_TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")
