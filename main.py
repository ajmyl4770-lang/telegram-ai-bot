import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN
from bot import chat

logging.basicConfig(level=logging.INFO)

# =========================
# 🟢 أوامر نصية
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في نظام أبو جميل التقني")

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 نظام VIP (Premium)\n\n"
        "- استخدام غير محدود\n"
        "- سرعة أعلى\n"
        "- دعم تقني أفضل\n\n"
        "للتفعيل تواصل مع الإدارة."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 البوت يعمل بشكل طبيعي")

# =========================
# 💬 الرسائل النصية
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
# 📷 تحليل الصور (مبدئي + جاهز للتطوير)
# =========================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        file_path = "image.jpg"
        await file.download_to_drive(file_path)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # 🔥 هنا حالياً رد ذكي مبدئي (نربطه لاحقاً بـ AI Vision)
        await update.message.reply_text(
            "📷 تم استلام الصورة\n\n"
            "🔍 لتحليلها بدقة:\n"
            "اكتب لي ماذا يظهر في الصورة أو المشكلة الموجودة، وسأعطيك الحل مباشرة."
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("⚠️ حدث خطأ أثناء معالجة الصورة")

# =========================
# 🚀 تشغيل البوت
# =========================

def main():
    print("🚀 BOT RUNNING")

    app = Application.builder().token(BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("stats", stats))

    # رسائل نصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    # 📷 صور
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_polling()

if __name__ == "__main__":
    main()
