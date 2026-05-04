import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# 🔥 عدد الرسائل في الذاكرة
MAX_HISTORY = 12

# إنشاء جدول الرسائل
cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT
)
""")

conn.commit()

# =========================
# 💾 حفظ رسالة
# =========================
def save(user_id, role, text):
    cur.execute(
        "INSERT INTO messages VALUES (?, ?, ?)",
        (user_id, role, text)
    )
    conn.commit()

# =========================
# 📖 جلب المحادثة
# =========================
def history(user_id):
    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (user_id, MAX_HISTORY)
    )
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
