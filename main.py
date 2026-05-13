import telebot
import config
import database as db
from ai import chat
from gtts import gTTS
import os
import traceback

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    db.create_user(user_id)

    text = f"""
👋 أهلاً بك يا أبو جميل 🌟

🤖 مركز بن علي للذكاء الصناعي

📌 الخدمات:

💬 دردشة ذكية
🎵 /music إنشاء أغنية
📊 /stats الإحصائيات
🧹 /clear مسح الذاكرة

✨ أرسل أي رسالة للبدء
"""

    bot.send_message(message.chat.id, text)

# =========================
# MUSIC
# =========================
@bot.message_handler(commands=['music'])
def music(message):

    user_id = str(message.chat.id)

    user_mode[user_id] = "music"

    bot.reply_to(
        message,
        "🎵 اكتب فكرة الأغنية\nمثال:\nشيلة حماس\nراب يمني\nاغنية حب"
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

    db.cur.execute(
        "DELETE FROM messages WHERE user_id=?",
        (user_id,)
    )

    db.conn.commit()

    bot.reply_to(message, "🧹 تم مسح المحادثة")

# =========================
# MAIN
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):

    user_id = str(message.chat.id)

    text = message.text

    try:

        db.create_user(user_id)

        db.reset_daily(user_id)

        mode = user_mode.get(user_id, "chat")

        # ================= MUSIC =================
        if mode == "music":

            bot.send_chat_action(
                message.chat.id,
                "upload_audio"
            )

            prompt = f"""
اكتب أغنية عربية قوية من 8 إلى 12 سطر

الستايل:
- راب
- شيلات
- شعبي
- خليجي
- يمني

بدون مبالغة
بدون تكرار

الموضوع:
{text}
"""

            try:

                lyrics = chat([
                    {
                        "role": "user",
                        "content": prompt
                    }
                ])

                file_name = f"{user_id}.mp3"

                tts = gTTS(
                    text=lyrics,
                    lang="ar"
                )

                tts.save(file_name)

                audio = open(file_name, "rb")

                bot.send_audio(
                    message.chat.id,
                    audio,
                    title="🎵 AI Song",
                    caption="🎧 تم إنشاء الأغنية"
                )

                audio.close()

                os.remove(file_name)

            except Exception as e:

                print("MUSIC ERROR:")
                print(e)
                traceback.print_exc()

                bot.reply_to(
                    message,
                    "⚠️ حدث خطأ أثناء إنشاء الأغنية"
                )

            user_mode[user_id] = None

            return

        # ================= CHAT =================

        history = db.history(user_id)

        history.append({
            "role": "user",
            "content": text
        })

        try:

            response = chat(history)

        except Exception as e:

            print("AI ERROR:")
            print(e)
            traceback.print_exc()

            response = "⚠️ الذكاء الاصطناعي مشغول حالياً"

        db.save(user_id, "user", text)

        db.save(user_id, "assistant", response)

        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:

        print("MAIN ERROR:")
        print(e)
        traceback.print_exc()

        bot.reply_to(
            message,
            "⚠️ حدث خطأ مؤقت"
        )

# =========================
# RUN
# =========================
print("🤖 Bot Running...")

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print("POLLING ERROR:")
        print(e)
