import io
from datetime import datetime

def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы для Telegram Markdown"""
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

def format_report(user_id, events):
    """Форматирует события в читаемый отчёт"""
    report_lines = [f"📋 Отчёт для пользователя {user_id}", f"📅 Период: {datetime.now().strftime('%d.%m.%Y')}", "", "=" * 50, ""]
    
    for event in events:
        date_str, event_type, value, severity, note = event
        
        try:
            if isinstance(date_str, str):
                created_at = datetime.fromisoformat(date_str)
            else:
                created_at = date_str
            time_str = created_at.strftime("%d.%m.%Y %H:%M")
        except:
            time_str = date_str[:16] if len(date_str) > 16 else date_str
        
        if event_type == "sleep":
            report_lines.append(f"🌙 Сон: {value} ч ({time_str})")
        elif event_type == "food":
            report_lines.append(f"🍽️ Еда: {value} ({time_str})")
        elif event_type == "meltdown":
            severity = severity or 0
            severity_str = "🔴" * severity + "⚪" * (5 - severity)
            report_lines.append(f"😭 Истерика: {severity}/5 {severity_str} ({time_str})")
            if note:
                report_lines.append(f"   📝 Причина: {note}")
        elif event_type == "toilet":
            emoji = "✅" if "успех" in str(value).lower() else "⚠️"
            report_lines.append(f"🚽 Туалет: {value} {emoji} ({time_str})")
        elif event_type == "mood":
            mood_emojis = {1: "😭", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}
            mood_emoji = mood_emojis.get(severity, "😐")
            report_lines.append(f"😊 Настроение: {mood_emoji} {severity}/5 ({time_str})")
        elif event_type == "behavior":
            behavior_type = value if value else (note if note else "не указан")
            severity_str = "🔴" * severity + "⚪" * (5 - severity)
            report_lines.append(f"😔 Поведение: {behavior_type} (сила {severity}/5) {severity_str} ({time_str})")
        else:
            report_lines.append(f"📌 {event_type}: {value} ({time_str})")
    
    return "\n".join(report_lines)

def create_report_file(report_text):
    """Создаёт файл с отчётом для отправки"""
    file_obj = io.BytesIO()
    file_obj.write(report_text.encode('utf-8'))
    file_obj.seek(0)
    file_obj.name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return file_obj

def get_random_tip(tips_list):
    """Возвращает случайный совет из списка"""
    import random
    if not tips_list:
        return "💡 Старайтесь соблюдать режим дня — это снижает тревожность."
    return random.choice(tips_list)
