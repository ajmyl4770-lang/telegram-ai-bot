import sqlite3
import time
from config import ADMIN_ID

DB_NAME = "bot.db"
MAX_HISTORY = 12

def get_db_connection():
    """توليد اتصال جديد وآمن لكل عملية برمجية منفصلة"""
    conn = sqlite3.connect(DB_NAME, timeout=10) # مهلة لمنع قفل البيانات عند الضغط
    return conn

def init_db():
    """إنشاء الجداول عند تشغيل الملف لأول مرة"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            vip INTEGER DEFAULT 0,
            daily_count INTEGER DEFAULT 0,
            last_reset INTEGER
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp INTEGER
        )
        """)
        conn.commit()

# تشغيل التهيئة تلقائياً عند استيراد الملف
init_db()

def create_user(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users VALUES (?,0,0,?)",
                (user_id, int(time.time()))
            )
            conn.commit()

def get_user(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone()

def reset_daily(user_id):
    u = get_user(user_id)
    if u and time.time() - u[3] > 86400:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET daily_count=0,last_reset=? WHERE user_id=?",
                (int(time.time()), user_id)
            )
            conn.commit()

def increase_count(user_id):
    if user_id == ADMIN_ID:
        return
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET daily_count=daily_count+1 WHERE user_id=?",
            (user_id,)
        )
        conn.commit()

def is_vip(user_id):
    u = get_user(user_id)
    return u and u[1] == 1

def save(user_id, role, text):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages VALUES (?,?,?,?)",
            (user_id, role, text, int(time.time()))
        )
        conn.commit()

def history(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role,content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
            (user_id, MAX_HISTORY)
        )
        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def clear_user_messages(user_id):
    """الدالة المضافة والآمنة لحذف محادثات مستخدم معين بالكامل"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
        conn.commit()
