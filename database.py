import sqlite3
from datetime import datetime, timedelta

from config import DATABASE_NAME

def get_connection():
    """Возвращает соединение с БД"""
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    """Создание таблиц при первом запуске"""
    with get_connection() as conn:
        c = conn.cursor()

        # Таблица пользователей
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Таблица событий
        c.execute('''CREATE TABLE IF NOT EXISTS events
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                event_type TEXT,
                value TEXT,
                severity INTEGER,
                note TEXT)''')


        # Таблица лекарств
        c.execute('''CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            dosage TEXT,
            start_date TEXT,
            end_date TEXT DEFAULT NULL,
            status TEXT DEFAULT 'active'
        )''')

        # Таблица приёмов лекарств
        c.execute('''CREATE TABLE IF NOT EXISTS medication_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id INTEGER,
            taken_date TEXT,
            reaction TEXT,
            side_effects TEXT,
            improvements TEXT,
            notes TEXT
        )''')

        conn.commit()

def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавление нового пользователя (если ещё не существует)"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name) 
                     VALUES (?, ?, ?)''',
                  (user_id, username, first_name))
        conn.commit()
def add_event(user_id: int, event_type: str, behavior_type: str = "", value: str = "", severity: int = None, note: str = ""):
    with get_connection() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO events
                (user_id, date, event_type, behavior_type, value, severity, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, now, event_type, behavior_type, value, severity, note))
        conn.commit()

def get_all_users():
    """Получение списка всех пользователей"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT user_id, username, first_name, created_at FROM users ORDER BY created_at DESC')
        return c.fetchall()

def add_event(user_id: int, event_type: str, value: str = "", severity: int = None, note: str = ""):
    """Добавление события"""
    with get_connection() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO events
                (user_id, date, event_type, value, severity, note)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, now, event_type, value, severity, note))
        conn.commit()

def add_medication(user_id: int, name: str, dosage: str, start_date: str):
    """Добавление нового лекарства"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO medications (user_id, name, dosage, start_date, status)
                     VALUES (?, ?, ?, ?, 'active')''',
                  (user_id, name, dosage, start_date))
        conn.commit()
        return c.lastrowid

def get_active_medications(user_id: int):
    """Список активных лекарств пользователя"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT id, name, dosage, start_date
                     FROM medications
                     WHERE user_id = ? AND status = 'active'
                     ORDER BY start_date DESC''', (user_id,))
        return c.fetchall()

def log_medication_take(medication_id: int, reaction: str, side_effects: str, improvements: str):
    """Запись о приёме лекарства"""
    with get_connection() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO medication_logs 
                     (medication_id, taken_date, reaction, side_effects, improvements)
                     VALUES (?, ?, ?, ?, ?)''',
                  (medication_id, now, reaction, side_effects, improvements))
        conn.commit()

def get_medication_by_id(medication_id: int, user_id: int):
    """Получить информацию о лекарстве по ID"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT id, name, dosage, start_date, end_date
                     FROM medications 
                     WHERE id = ? AND user_id = ?''', (medication_id, user_id))
        return c.fetchone()

def get_medication_logs(medication_id: int):
    """Получить все записи о приёме лекарства"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT taken_date, reaction, side_effects, improvements
                     FROM medication_logs 
                     WHERE medication_id = ?
                     ORDER BY taken_date DESC''', (medication_id,))
        return c.fetchall()

def get_stats(user_id: int, days: int = 7):
    """Получение статистики за последние N дней"""
    with get_connection() as conn:
        c = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('''SELECT COUNT(*), AVG(severity)
                FROM events
                WHERE user_id=? AND event_type='meltdown' AND date>?''',
                  (user_id, since_date))
        meltdown_count, avg_severity = c.fetchone()

        c.execute('''SELECT value FROM events 
                     WHERE user_id=? AND event_type='sleep' AND date>? 
                     ORDER BY date DESC LIMIT 5''',
                  (user_id, since_date))
        sleep_records = c.fetchall()

        c.execute('''SELECT note FROM events 
                     WHERE user_id=? AND event_type='meltdown' 
                     AND note!='' AND date>?''',
                  (user_id, since_date))
        reasons = c.fetchall()

        return {
            'meltdown_count': meltdown_count or 0,
            'avg_severity': round(avg_severity, 1) if avg_severity else 0,
            'sleep_records': [r[0] for r in sleep_records],
            'reasons': [r[0] for r in reasons]
        }

def get_events_for_report(user_id: int, days: int = 30):
    """Получение событий для отчета врачу"""
    with get_connection() as conn:
        c = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT date, event_type, value, severity, note 
                     FROM events 
                     WHERE user_id=? AND date>? 
                     ORDER BY date DESC''',
                  (user_id, since_date))
        return c.fetchall()

def add_reminder(user_id: int, reminder_time, message: str):
    """Добавление напоминания в БД"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO reminders (user_id, reminder_time, message, is_active) 
                     VALUES (?, ?, ?, 1)''',
                  (user_id, reminder_time.isoformat(), message))
        conn.commit()
        return c.lastrowid

def get_due_reminders():
    """Получить напоминания, которые пора отправить и ещё не отправлены"""
    with get_connection() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''SELECT id, user_id, message FROM reminders 
                     WHERE reminder_time <= ? AND is_active = 1''', (now,))
        return c.fetchall()

def mark_reminder_sent(reminder_id: int):
    """Отметить напоминание как отправленное"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE reminders SET is_active = 0 WHERE id = ?', (reminder_id,))
        conn.commit()

def update_last_meltdown_reason(user_id: int, reason: str):
    """Обновление причины последней истерики"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''UPDATE events 
                     SET note=? 
                     WHERE user_id=? AND event_type='meltdown' 
                     ORDER BY date DESC LIMIT 1''',
                  (reason, user_id))
        conn.commit()
