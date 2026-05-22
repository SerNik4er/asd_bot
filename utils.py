import io
from datetime import datetime
from telegram import BufferedInputFile

def format_report(user_id, events):
    """Форматирует события в читаемый отчёт"""
    report_lines = [f"📋 Отчёт для пользователя {user_id}", f"📅 Период: {datetime.now().strftime('%d.%m.%Y')}", "", "=" * 50, ""]
    
    for event in events:
        event_type, value, severity, created_at = event
        time_str = created_at.strftime("%d.%m.%Y %H:%M")
        
        if event_type == "sleep":
            report_lines.append(f"🌙 Сон: {value} ч ({time_str})")
        elif event_type == "food":
            report_lines.append(f"🍽️ Еда: {value} ({time_str})")
        elif event_type == "meltdown":
            severity_str = "🔴" * severity + "⚪" * (5 - severity)
            report_lines.append(f"😭 Истерика: {severity}/5 {severity_str} ({time_str})")
        elif event_type == "toilet":
            emoji = "✅" if "успех" in value.lower() else "⚠️"
            report_lines.append(f"🚽 Туалет: {value} {emoji} ({time_str})")
        elif event_type == "mood":
            mood_emojis = {1: "😭", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}
            mood_emoji = mood_emojis.get(severity, "😐")
            report_lines.append(f"😊 Настроение: {mood_emoji} {severity}/5 ({time_str})")
    
    return "\n".join(report_lines)

def create_report_file(report_text):
    """Создаёт файл с отчётом для отправки"""
    file_obj = io.BytesIO()
    file_obj.write(report_text.encode('utf-8'))
    file_obj.seek(0)
    return BufferedInputFile(file_obj.getvalue(), filename=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def get_random_tip(tips_list):
    """Возвращает случайный совет из списка"""
    import random
    if not tips_list:
        return "💡 Старайтесь соблюдать режим дня — это снижает тревожность."
    return random.choice(tips_list)
