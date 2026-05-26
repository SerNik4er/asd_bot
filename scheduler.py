import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Bot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def schedule_reminder(bot_token: str, chat_id: int, message: str, reminder_time):
    """Планирует отправку напоминания"""
    
    async def send_reminder():
        try:
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=chat_id,
                text=f"🔔 *Напоминание!*\n\n{message}",
                parse_mode="Markdown"
            )
            logger.info(f"Reminder sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    def run_async():
        asyncio.run(send_reminder())
    
    scheduler.add_job(
        run_async,
        trigger=DateTrigger(run_date=reminder_time),
        id=f"reminder_{chat_id}_{reminder_time.timestamp()}",
        replace_existing=True
    )
    logger.info(f"Reminder scheduled for {reminder_time}")

def start_scheduler():
    scheduler.start()
    logger.info("Scheduler started")

def stop_scheduler():
    scheduler.shutdown()
