import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN
from bot import chat

logging.basicConfig(level=logging.INFO)

# =========================
# 🟢 أوامر البوت
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في أبو جميل")

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 نظام VIP:\n"
        "- استخدام غير محدود\n"
        "- سرعة أعلى\n"
        "- أولوية في الرد\n\n"
        "للتفعيل تواصل مع الإدارة."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 البوت يعمل بشكل طبيعي حالياً.")

# =========================
# 💬 الرسائل
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        reply = chat(user_id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("⚠️ خطأ، حاول لاحقاً")

# =========================
# 🚀 تشغيل البوت
# =========================

def main():
    print("🚀 BOT RUNNING")

    app = Application.builder().token(BOT_TOKEN).build()

    # أوامر أساسية
    app.add_handler(CommandHandler("start", start))

    # 💎 أوامر احترافية
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("stats", stats))

    # الرسائل العادية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()

if __name__ == "__main__":
    main()
