from datetime import datetime
from io import BytesIO
from aiogram.types import BufferedInputFile
import random

def format_report(user_id: str, events):
    """Форматирование отчета для врача"""
    report = f"Отчет для врача\nДата: {datetime.now().strftime('%d.%m.%Y')}\n"
    report += "=" * 49 + "\n\n"

    current_date = ""
    for event in events:
        event_date = event[0][:10]
        if current_date != event_date:
            report += f"\n📅 {event_date}:\n"
            current_date = event_date

        event_type_emoji = {
            "sleep": "🌙", "food": "🍎", "toilet": "🚽", "meltdown": "😭", "mood": "😊"}.get(event[1], "📝")

        report += f" {event_type_emoji} {event[1]}: "
        if event[3]:
            report += f"сила {event[3]}/5"
        else:
            report += f" ({event[4]})"
        report += "/n"
    return report

def create_report_file(report_text: str):
    """Создание файла с отчетом"""
    file = BytesIO(report_text.encode('utf-8'))
    file.name = f"report_{datetime.now().strftime('%Y%m%d')}.txt"
    return BufferedInputFile(file.getvalue(), filename=file.name)

def get_random_tip(tips_list):
    """Получение случайного совета"""
    return random.choice(tips_list)