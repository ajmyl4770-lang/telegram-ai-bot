import sqlite3
import time

# الاتصال بقاعدة البيانات
conn = sqlite3.connect("users_data.db", check_same_thread=False)
cur = conn.cursor()

FREE_LIMIT = 20
MAX_HISTORY = 12

# إنشاء الجداول
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    vip INTEGER DEFAULT 0,
    daily_count INTEGER DEFAULT 0,
    last_reset INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp INTEGER
)
""")
conn.commit()

def create_user(user_id):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES (?, 0, 0, ?)", (user_id, int(time.time())))
        conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def reset_daily(user_id):
    user = get_user(user_id)
    if user and time.time() - user[3] > 86400:
        cur.execute("UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?", (int(time.time()), user_id))
        conn.commit()

def increase_count(user_id):
    cur.execute("UPDATE users SET daily_count = daily_count + 1 WHERE user_id=?", (user_id,))
    conn.commit()

def is_vip(user_id):
    user = get_user(user_id)
    return user and user[1] == 1

def save_chat(user_id, role, text):
    cur.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (user_id, role, text, int(time.time())))
    conn.commit()

def get_history(user_id):
    cur.execute("SELECT role, content FROM history WHERE user_id=? ORDER BY rowid DESC LIMIT ?", (user_id, MAX_HISTORY))
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
