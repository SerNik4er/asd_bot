import sqlite3
from datetime import datetime, timedelta

#from apscheduler.schedulers.gevent import GeventScheduler

from config import DATABASE_NAME

def get_connection():
    """Возвращает соединение с БД"""
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    """Создание таблиц при первом запуске"""
    with get_connection() as conn:
        c = conn.cursor()

        # Таблица событий
        c.execute('''CREATE TABLE IF NOT EXISTS events
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                event_type TEXT,
                value TEXT,
                severity INTEGER,
                note TEXT)''')

        #Таблица напоминаний
        c.execute('''CREATE TABLE IF NOT EXISTS reminders
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_time TEXT,
                message TEXT,
                is_active INTEGER DEFAULT 1)''')

        conn.commit()

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

def get_stats(user_id: int, days: int = 7):
    """Получение статистики за последние N дней"""
    with get_connection() as conn:
        c = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Статистика по истерикам
        c.execute('''SELECT COUNT(*), AVG(severity)
                FROM events
                WHERE user_id=? AND event_type='meltdown' AND date>?''',
                  (user_id, since_date))
        meltdown_count, avg_severity = c.fetchone()

        # Статистика по сну
        c.execute('''SELECT value FROM events 
                     WHERE user_id=? AND event_type='sleep' AND date>? 
                     ORDER BY date DESC LIMIT 5''',
                  (user_id, since_date))
        sleep_records = c.fetchall()

        # Причины истерик
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
        c.execute('''INSERT INTO reminders (user_id, reminder_time, message) 
                     VALUES (?, ?, ?)''',
                  (user_id, reminder_time.isoformat(), message))
        conn.commit()
        return c.lastrowid

def get_active_reminders():
    """Получение всех активных напоминаний"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''SELECT id, user_id, reminder_time, message 
                     FROM reminders 
                     WHERE is_active=1''')
        return c.fetchall()

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