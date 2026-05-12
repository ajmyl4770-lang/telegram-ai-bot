import telebot
import config
import database as db
from ai import chat
import time

bot = telebot.TeleBot(config.BOT_TOKEN)

# =========================
# /start
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)

    db.create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 مرحباً بك!\nأنا بوت ذكاء اصطناعي متطور.\nارسل أي سؤال وسأساعدك."
    )


# =========================
# /stats
# =========================
@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = str(message.chat.id)
    user = db.get_user(user_id)

    if not user:
        bot.reply_to(message, "لا يوجد بيانات")
        return

    text = f"""
📊 إحصائياتك:

👤 المستخدم: {user_id}
💬 عدد الرسائل: {user[2]}
⭐ VIP: {'نعم' if user[1] else 'لا'}
"""

    bot.reply_to(message, text)


# =========================
# /clear
# =========================
@bot.message_handler(commands=['clear'])
def clear(message):
    user_id = str(message.chat.id)

    db.cur.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
    db.conn.commit()

    bot.reply_to(message, "🧹 تم مسح المحادثة بنجاح")


# =========================
# منع سبام بسيط
# =========================
last_msg = {}


# =========================
# الذكاء الاصطناعي
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    try:
        # منع السبام
        if user_id in last_msg:
            if time.time() - last_msg[user_id] < 2:
                return
        last_msg[user_id] = time.time()

        db.create_user(user_id)
        db.reset_daily(user_id)

        user = db.get_user(user_id)
        if not user:
            user = (user_id, 0, 0, 0)

        FREE_LIMIT = 20

        if not db.is_vip(user_id) and user[1] >= FREE_LIMIT:
            bot.reply_to(message, "❌ وصلت الحد اليومي (20 رسالة).")
            return

        history = db.history(user_id)
        history.append({"role": "user", "content": message.text})

        try:
            response = chat(history)
        except:
            response = "⚠️ حدث خطأ في الذكاء الاصطناعي"

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "⚠️ خطأ مؤقت، حاول لاحقاً.")


# =========================
# تشغيل البوت
# =========================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
