from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Bot
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def schedule_reminder(bot_token: str, chat_id: int, message: str, reminder_time, reminder_id: int):
    """Планирует отправку напоминания"""
    
    async def send_reminder():
        try:
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=chat_id,
                text=f"🔔 *Напоминание!*\n\n{message}",
                parse_mode="Markdown"
            )
            logger.info(f"Reminder {reminder_id} sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder_id}: {e}")
    
    scheduler.add_job(
        lambda: asyncio.run(send_reminder()),
        trigger=DateTrigger(run_date=reminder_time),
        id=f"reminder_{reminder_id}",
        replace_existing=True
    )
    logger.info(f"Reminder {reminder_id} scheduled for {reminder_time}")

def start_scheduler():
    scheduler.start()
    logger.info("Scheduler started")

def stop_scheduler():
    scheduler.shutdown()
