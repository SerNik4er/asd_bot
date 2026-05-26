from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, DATABASE_NAME
from utils import escape_markdown
import sqlite3

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка, что команду вызвал администратор
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return

    try:
        # Подключаемся к базе данных через путь из config
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Получаем данные о пользователях
        cursor.execute("SELECT user_id, username, first_name, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        conn.close()

        if not users:
            await update.message.reply_text("📭 Пользователей пока нет.")
            return

        # Формируем красивое сообщение (без Markdown, чтобы избежать ошибок)
        message_text = "👥 *Список пользователей:*\n\n"
        for user in users:
            user_id, username, first_name, created_at = user
            name_part = escape_markdown(first_name) if first_name else "Без имени"
            username_part = f"(@{escape_markdown(username)})" if username else ""
            message_text += f"• {name_part} {username_part} — ID: `{user_id}`\n"

        await update.message.reply_text(message_text, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении данных: {e}")
