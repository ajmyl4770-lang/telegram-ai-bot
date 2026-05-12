import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0,
    last_reset INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    role TEXT,
    message TEXT
)
""")

conn.commit()


def create_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()


def is_vip(user_id):
    user = get_user(user_id)
    return user and user[3] == 1


def reset_daily(user_id):
    user = get_user(user_id)
    if not user:
        return

    now = int(time.time())
    if now - user[2] > 86400:
        cur.execute("UPDATE users SET count=0, last_reset=? WHERE user_id=?", (now, user_id))
        conn.commit()


def increase_count(user_id):
    cur.execute("UPDATE users SET count = count + 1 WHERE user_id=?", (user_id,))
    conn.commit()


def save(user_id, role, message):
    cur.execute(
        "INSERT INTO history (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )
    conn.commit()


def history(user_id):
    cur.execute("SELECT role, message FROM history WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    rows = cur.fetchall()

    return [
        {"role": role, "content": msg}
        for role, msg in reversed(rows)
    ]
