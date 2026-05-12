import telebot
from telebot import types
import config
import database as db
from ai import chat
import time

bot = telebot.TeleBot(config.BOT_TOKEN)

# =========================
# منع السبام
# =========================
last_msg = {}

# =========================
# أوضاع المستخدم
# =========================
user_mode = {}

# =========================
# القائمة الرئيسية
# =========================
def main_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    btn1 = types.KeyboardButton("💬 دردشة")
    btn2 = types.KeyboardButton("🖼️ صورة")
    btn3 = types.KeyboardButton("🎵 أغنية")
    btn4 = types.KeyboardButton("📊 إحصائياتي")
    btn5 = types.KeyboardButton("🧹 مسح الذاكرة")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)

    return markup


# =========================
# /start
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    db.create_user(user_id)

    text = """
👋 أهلاً وسهلاً بك يا أبو جميل 🌟

🤖 أنا مساعدك الذكي المتطور.

📌 الخدمات المتاحة:

💬 دردشة ذكية
🖼️ إنشاء صور
🎵 كتابة أغاني
📊 عرض الإحصائيات
🧹 مسح الذاكرة

✨ اختر من الأزرار بالأسفل
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# =========================
# الإحصائيات
# =========================
@bot.message_handler(func=lambda m: m.text == "📊 إحصائياتي")
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
# مسح الذاكرة
# =========================
@bot.message_handler(func=lambda m: m.text == "🧹 مسح الذاكرة")
def clear(message):

    user_id = str(message.chat.id)

    db.cur.execute(
        "DELETE FROM messages WHERE user_id=?",
        (user_id,)
    )

    db.conn.commit()

    bot.reply_to(
        message,
        "✅ تم مسح المحادثة بنجاح"
    )


# =========================
# وضع الصور
# =========================
@bot.message_handler(func=lambda m: m.text == "🖼️ صورة")
def image_info(message):

    user_id = str(message.chat.id)

    user_mode[user_id] = "image"

    bot.reply_to(
        message,
        "🖼️ اكتب وصف الصورة مباشرة"
    )


# =========================
# وضع الأغاني
# =========================
@bot.message_handler(func=lambda m: m.text == "🎵 أغنية")
def music_info(message):

    user_id = str(message.chat.id)

    user_mode[user_id] = "music"

    bot.reply_to(
        message,
        "🎵 اكتب فكرة الأغنية مباشرة"
    )


# =========================
# دردشة
# =========================
@bot.message_handler(func=lambda m: m.text == "💬 دردشة")
def ai_info(message):

    user_id = str(message.chat.id)

    user_mode[user_id] = "chat"

    bot.reply_to(
        message,
        "💬 ارسل أي رسالة وسأرد عليك"
    )


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

        if not db.is_vip(user_id) and user[2] >= FREE_LIMIT:

            bot.reply_to(
                message,
                "❌ وصلت الحد اليومي (20 رسالة)"
            )

            return

        # =========================
        # وضع الأغاني
        # =========================
        if user_mode.get(user_id) == "music":

            bot.send_chat_action(
                message.chat.id,
                "typing"
            )

            prompt = f"""
اكتب أغنية عربية جميلة ومؤثرة عن:
{message.text}
"""

            history = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = chat(history)

            bot.reply_to(message, response)

            user_mode[user_id] = None

            return

        # =========================
        # وضع الصور
        # =========================
        if user_mode.get(user_id) == "image":

            bot.reply_to(
                message,
                f"🎨 جاري إنشاء الصورة:\n\n{message.text}"
            )

            user_mode[user_id] = None

            return

        # =========================
        # الدردشة العادية
        # =========================
        history = db.history(user_id)

        history.append({
            "role": "user",
            "content": message.text
        })

        bot.send_chat_action(
            message.chat.id,
            "typing"
        )

        try:

            response = chat(history)

        except Exception as e:

            print("AI ERROR:", e)

            response = "⚠️ حدث خطأ في الذكاء الاصطناعي"

        db.save(
            user_id,
            "user",
            message.text
        )

        db.save(
            user_id,
            "assistant",
            response
        )

        db.increase_count(user_id)

        bot.reply_to(
            message,
            response
        )

    except Exception as e:

        print("ERROR:", e)

        bot.reply_to(
            message,
            "⚠️ حدث خطأ مؤقت"
        )


# =========================
# تشغيل البوت
# =========================
print("🤖 Bot is running...")

bot.infinity_polling(
    skip_pending=True
)
