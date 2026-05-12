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
    "👋 أهلاً وسهلاً بك يا أبو جميل 🌟\n\n"
    "🤖 أنا مساعدك الذكي المتطور.\n"
    "جاهز لمساعدتك في أي وقت.\n\n"

    "📌 الأوامر المتاحة:\n\n"

    "🖼️ /img → إنشاء صورة\n"
    "🎵 /music → كتابة أغنية\n"
    "🎬 /video → إنشاء فكرة فيديو\n"
    "🧹 /clear → مسح المحادثة\n"
    "📊 /stats → الإحصائيات\n\n"

    "💡 فقط أرسل رسالتك وسأهتم بالباقي ✨"
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

    db.cur.execute(
        "DELETE FROM messages WHERE user_id=?",
        (user_id,)
    )
    db.conn.commit()

    bot.reply_to(message, "🧹 تم مسح المحادثة بنجاح")


# =========================
# /img
# =========================
@bot.message_handler(commands=['img'])
def generate_image(message):
    prompt = message.text.replace("/img", "").strip()

    if not prompt:
        bot.reply_to(
            message,
            "🖼️ اكتب وصف الصورة بعد الأمر /img"
        )
        return

    bot.reply_to(
        message,
        f"🎨 جاري إنشاء صورة:\n{prompt}"
    )


# =========================
# /music
# =========================
@bot.message_handler(commands=['music'])
def music(message):
    text = message.text.replace("/music", "").strip()

    if not text:
        bot.reply_to(
            message,
            "🎵 اكتب فكرة الأغنية بعد /music"
        )
        return

    prompt = f"اكتب كلمات أغنية عربية جميلة عن: {text}"

    history = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = chat(history)

    bot.reply_to(message, response)


# =========================
# /video
# =========================
@bot.message_handler(commands=['video'])
def video(message):
    prompt = message.text.replace("/video", "").strip()

    if not prompt:
        bot.reply_to(
            message,
            "🎬 اكتب وصف الفيديو بعد /video"
        )
        return

    bot.reply_to(
        message,
        f"🎬 ميزة الفيديو قيد التطوير.\n\nالوصف:\n{prompt}"
    )


# =========================
# منع السبام
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

        if not db.is_vip(user_id) and user[2] >= FREE_LIMIT:
            bot.reply_to(
                message,
                "❌ وصلت للحد اليومي (20 رسالة)"
            )
            return

        history = db.history(user_id)

        history.append({
            "role": "user",
            "content": message.text
        })

        try:
            response = chat(history)
        except Exception as e:
            print("AI ERROR:", e)
            response = "⚠️ حدث خطأ في الذكاء الاصطناعي"

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)

        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)

        bot.reply_to(
            message,
            "⚠️ حدث خطأ مؤقت، حاول لاحقاً"
        )


# =========================
# تشغيل البوت
# =========================
print("🤖 Bot is running...")

bot.infinity_polling(skip_pending=True)
