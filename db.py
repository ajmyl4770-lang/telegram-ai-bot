import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

MAX_HISTORY = 12

# الرسائل
cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp INTEGER
)
""")

# المستخدمين
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    first_seen INTEGER,
    last_seen INTEGER
)
""")

conn.commit()

# =========================
# حفظ رسالة
# =========================
def save(user_id, role, text):
    cur.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (user_id, role, text, int(time.time()))
    )
    conn.commit()

# =========================
# جلب الذاكرة
# =========================
def history(user_id):
    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, MAX_HISTORY)
    )
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

# =========================
# تسجيل المستخدم
# =========================
def touch_user(user_id):
    now = int(time.time())

    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (user_id, now, now)
        )
    else:
        cur.execute(
            "UPDATE users SET last_seen=? WHERE user_id=?",
            (now, user_id)
        )

    conn.commit()
