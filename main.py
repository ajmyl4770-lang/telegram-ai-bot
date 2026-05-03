import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

logging.basicConfig(level=logging.INFO)

# 🔐 من البيئة (GitHub + Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise Exception("Missing API Keys")

client = Groq(api_key=GROQ_API_KEY)

MAX_HISTORY = 8
SYSTEM_PROMPT = "أنت مساعد ذكي عربي اسمه أبو جميل من مركز بن علي."

# ================= DB =================
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

# ================= HELPERS =================
def save(uid, role, text):
    cur.execute("INSERT INTO messages VALUES (?, ?, ?)", (uid, role, text))
    conn.commit()

def history(uid):
    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT ?",
        (uid, MAX_HISTORY)
    )
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

# ================= BOT =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في البوت الاحترافي")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    text = update.message.text

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    try:
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + history(user_id)
            + [{"role": "user", "content": text}]
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        save(user_id, "user", text)
        save(user_id, "assistant", reply)

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("⚠️ حدث خطأ، حاول لاحقاً")

def main():
    print("🚀 BOT STARTED")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()

if __name__ == "__main__":
    main()
