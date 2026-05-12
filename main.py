import telebot
import config
import database as db
from ai import chat
from telebot import types
import time

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}
last_msg_time = {}


# =========================
# القائمة الرئيسية
# =========================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("💬 دردشة", "🖼️ صورة")
    markup.row("🎵 أغنية", "📊 إحصائياتي")
    markup.row("🧹 مسح الذاكرة")

    return markup


# =========================
# /start
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    db.create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 أهلاً وسهلاً بك يا أبو جميل 🌟\n\n🤖 أنا مساعدك الذكي.",
        reply_markup=main_menu()
    )


# =========================
# الأزرار
# =========================
@bot.message_handler(func=lambda m: m.text == "💬 دردشة")
def chat_mode(message):
    user_mode[str(message.chat.id)] = "chat"
    bot.reply_to(message, "💬 اكتب رسالتك")


@bot.message_handler(func=lambda m: m.text == "🖼️ صورة")
def image_mode(message):
    user_mode[str(message.chat.id)] = "image"
    bot.reply_to(message, "🖼️ اكتب وصف الصورة")


@bot.message_handler(func=lambda m: m.text == "🎵 أغنية")
def music_mode(message):
    user_mode[str(message.chat.id)] = "music"
    bot.reply_to(message, "🎵 اكتب فكرة الأغنية")


@bot.message_handler(func=lambda m: m.text == "📊 إحصائياتي")
def stats(message):

    user_id = str(message.chat.id)
    user = db.get_user(user_id)

    if not user:
        bot.reply_to(message, "لا يوجد بيانات")
        return

    bot.reply_to(message,
        f"📊 إحصائياتك:\n\n💬 الرسائل: {user[2]}\n⭐ VIP: {'نعم' if user[1] else 'لا'}"
    )


@bot.message_handler(func=lambda m: m.text == "🧹 مسح الذاكرة")
def clear(message):

    user_id = str(message.chat.id)

    db.cur.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
    db.conn.commit()

    bot.reply_to(message, "🧹 تم مسح الذاكرة")


# =========================
# الذكاء الاصطناعي
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):

    user_id = str(message.chat.id)

    try:

        # منع سبام بسيط
        if user_id in last_msg_time:
            if time.time() - last_msg_time[user_id] < 2:
                return

        last_msg_time[user_id] = time.time()

        db.create_user(user_id)
        db.reset_daily(user_id)

        user = db.get_user(user_id)

        if not user:
            user = (user_id, 0, 0, 0)

        FREE_LIMIT = 20

        if not db.is_vip(user_id) and user[2] >= FREE_LIMIT:
            bot.reply_to(message, "❌ انتهى الحد اليومي")
            return

        mode = user_mode.get(user_id, "chat")

        # =========================
        # الأغاني
        # =========================
        if mode == "music":

            bot.send_chat_action(message.chat.id, "typing")

            prompt = f"""
أنت كاتب أغاني عربي محترف (ليس شاعر عادي).

اكتب أغنية بأسلوب راب أو شعبي.

- بدون مدح أشخاص
- بدون مبالغة
- 8 إلى 12 سطر
- قصة أو إحساس واقعي

الموضوع:
{message.text}
"""

            response = chat([{"role": "user", "content": prompt}])

            bot.reply_to(message, response)

            user_mode[user_id] = None
            return

        # =========================
        # الصور (مبدئي)
        # =========================
        if mode == "image":

            bot.reply_to(message, f"🖼️ جاري إنشاء صورة: {message.text}")

            user_mode[user_id] = None
            return

        # =========================
        # الدردشة
        # =========================
        history = db.history(user_id)
        history.append({"role": "user", "content": message.text})

        bot.send_chat_action(message.chat.id, "typing")

        response = chat(history)

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "⚠️ خطأ مؤقت")


print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
