import os
import telebot
import config
import database as db
from ai import chat
from gtts import gTTS

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}


# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)

    db.create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 أهلاً وسهلاً بك يا أبو جميل 🌟\n\n"
        "🤖 أنا مساعدك الذكي المتطور.\n\n"
        "📌 الأوامر:\n"
        "/music - أغنية\n"
        "/stats - إحصائيات\n"
        "/clear - مسح الذاكرة\n\n"
        "💬 فقط ارسل رسالتك وأنا أساعدك ✨"
    )


# =========================
# STATS
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

👤 ID: {user_id}
💬 الرسائل: {user[2]}
⭐ VIP: {'نعم' if user[1] else 'لا'}
"""

    bot.reply_to(message, text)


# =========================
# CLEAR
# =========================
@bot.message_handler(commands=['clear'])
def clear(message):
    user_id = str(message.chat.id)

    db.cur.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
    db.conn.commit()

    bot.reply_to(message, "🧹 تم مسح الذاكرة")


# =========================
# MUSIC MODE
# =========================
@bot.message_handler(commands=['music'])
def music_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "music"

    bot.reply_to(message, "🎵 اكتب فكرة الأغنية الآن")


# =========================
# MAIN HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    try:
        db.create_user(user_id)
        db.reset_daily(user_id)

        user = db.get_user(user_id)
        if not user:
            user = (user_id, 0, 0, 0)

        # تحديد الوضع
        mode = user_mode.get(user_id, "chat")

        # =========================
        # MUSIC MODE
        # =========================
        if mode == "music":

            bot.send_chat_action(message.chat.id, "upload_audio")

            prompt = f"""
اكتب أغنية عربية قصيرة (8 إلى 12 سطر)
أسلوب راب أو شعبي
بدون مبالغة أو تكرار

الموضوع:
{message.text}
"""

            lyrics = chat([{"role": "user", "content": prompt}])

            # توليد صوت
            file_path = f"{user_id}_song.mp3"
            tts = gTTS(text=lyrics, lang="ar")
            tts.save(file_path)

            # إرسال الأغنية
            with open(file_path, "rb") as audio:
                bot.send_audio(
                    message.chat.id,
                    audio,
                    title="🎵 AI Song",
                    caption="🎧 تم إنشاء أغنية بالذكاء الاصطناعي"
                )

            os.remove(file_path)
            user_mode[user_id] = None
            return

        # =========================
        # CHAT MODE
        # =========================
        if not db.is_vip(user_id) and user[2] >= config.FREE_LIMIT:
            bot.reply_to(message, "❌ وصلت الحد اليومي")
            return

        history = db.history(user_id)
        history.append({"role": "user", "content": message.text})

        response = chat(history)

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "⚠️ حصل خطأ")


# =========================
# START BOT
# =========================
print("🤖 Bot is running...")
bot.infinity_polling()
