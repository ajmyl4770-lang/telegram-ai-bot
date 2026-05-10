ADMIN_ID = "1710957371"  # حط User ID حقك هنا
import sqlite3
import time

# =========================
# اتصال قاعدة البيانات
# =========================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

MAX_HISTORY = 12
FREE_LIMIT = 20  # عدد الرسائل المجانية يوميًا

# =========================
# إنشاء الجداول
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    vip INTEGER DEFAULT 0,
    daily_count INTEGER DEFAULT 0,
    last_reset INTEGER
)
""")

conn.commit()

# =========================
# المستخدمين
# =========================

def create_user(user_id):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users VALUES (?, 0, 0, ?)",
            (user_id, int(time.time()))
        )
        conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def reset_daily(user_id):
    user = get_user(user_id)
    if user and time.time() - user[3] > 86400:
        cur.execute(
            "UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?",
            (int(time.time()), user_id)
        )
        conn.commit()
def increase_count(user_id):
    if user_id == ADMIN_ID:
        return  # 👑 أنت مستثنى

    cur.execute(
        "UPDATE users SET daily_count = daily_count + 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()

# =========================
# VIP SYSTEM
# =========================

def set_vip(user_id):
    cur.execute("UPDATE users SET vip=1 WHERE user_id=?", (user_id,))
    conn.commit()

def remove_vip(user_id):
    cur.execute("UPDATE users SET vip=0 WHERE user_id=?", (user_id,))
    conn.commit()

def is_vip(user_id):
    user = get_user(user_id)
    if user:
        return user[1] == 1
    return False

# =========================
# الرسائل (ذاكرة المحادثة)
# =========================

def save(user_id, role, text):
    cur.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (user_id, role, text, int(time.time()))
    )
    conn.commit()

def history(user_id):
    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, MAX_HISTORY)
    )
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
