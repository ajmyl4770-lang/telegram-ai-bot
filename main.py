import os
import telebot
from gtts import gTTS

import config
import database as db
from ai import chat

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
👋 أهلاً وسهلاً بك يا {message.from_user.first_name or 'أبو جميل'} 🌟

🤖 أنا مساعدك الذكي المتطور.

📌 الخدمات:
💬 دردشة
🎵 /music
🖼️ /img (قريباً)
📊 /stats
🧹 /clear

✨ فقط اكتب رسالتك
"""
    bot.send_message(message.chat.id, text)


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

    bot.reply_to(message, "🧹 تم مسح المحادثة")


# =========================
# MUSIC MODE
# =========================
@bot.message_handler(commands=['music'])
def music_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "music"

    bot.reply_to(message,
        "🎵 أرسل فكرة الأغنية الآن\n"
        "مثال: اغنية حزينة عن الفراق أو حب"
    )


# =========================
# IMAGE (مستقبلاً)
# =========================
@bot.message_handler(commands=['img'])
def img(message):
    bot.reply_to(message, "🖼️ ميزة الصور قيد التطوير")


# =========================
# MAIN CHAT HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    db.create_user(user_id)
    db.reset_daily(user_id)

    user = db.get_user(user_id)
    if not user:
        user = (user_id, 0, 0, 0)

    # ============ MUSIC MODE ============
    if user_mode.get(user_id) == "music":

        bot.send_chat_action(message.chat.id, "upload_audio")

        prompt = f"""
أنت كاتب أغاني عربي محترف.

اكتب أغنية راب أو شعبية قوية (8-12 سطر فقط)

بدون مبالغة أو مدح زائد

الموضوع:
{message.text}
"""

        try:
            lyrics = chat([{"role": "user", "content": prompt}])

            # ===== TTS =====
            tts_file = f"{user_id}_voice.mp3"
            tts = gTTS(text=lyrics, lang="ar")
            tts.save(tts_file)

            # ===== SEND AUDIO =====
            audio = open(tts_file, "rb")

            bot.send_audio(
                message.chat.id,
                audio,
                title="🎵 AI Song",
                caption="✨ تم إنشاء أغنية بالذكاء الاصطناعي"
            )

            audio.close()
            os.remove(tts_file)

        except Exception as e:
            print("MUSIC ERROR:", e)
            bot.reply_to(message, "⚠️ حصل خطأ في إنشاء الأغنية")

        user_mode[user_id] = None
        return

    # ============ NORMAL CHAT ============
    try:
        history = db.history(user_id)
        history.append({"role": "user", "content": message.text})

        response = chat(history)

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "⚠️ خطأ مؤقت")


print("🤖 Bot is running...")
bot.polling()
