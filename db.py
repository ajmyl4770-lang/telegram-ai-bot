import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT
)
""")

conn.commit()

def save(user_id, role, text):
    cur.execute("INSERT INTO messages VALUES (?, ?, ?)", (user_id, role, text))
    conn.commit()

def history(user_id, limit=10):
    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, limit)
    )
    return [{"role": r[0], "content": r[1]} for r in reversed(cur.fetchall())]
