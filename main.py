import telebot
import config
import database as db
from ai import chat
from gtts import gTTS
from pydub import AudioSegment
import os

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    db.create_user(user_id)

    bot.send_message(message.chat.id,
        f"""👋 أهلاً بك يا أبو جميل 🌟

🤖 أنا مساعدك الذكي

📌 الأوامر:
🎵 /music
💬 دردشة عادية
📊 /stats
🧹 /clear
"""
    )

# =========================
# MUSIC MODE
# =========================
@bot.message_handler(commands=['music'])
def music(message):
    user_mode[str(message.chat.id)] = "music"
    bot.reply_to(message, "🎵 اكتب فكرة الأغنية الآن (خليجي - مصري - يمني - شيلات)")

# =========================
# CLEAR
# =========================
@bot.message_handler(commands=['clear'])
def clear(message):
    user_id = str(message.chat.id)
    db.cur.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
    db.conn.commit()
    bot.reply_to(message, "🧹 تم المسح")

# =========================
# STATS
# =========================
@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = str(message.chat.id)
    user = db.get_user(user_id)

    bot.reply_to(message,
        f"""📊 إحصائياتك:
💬 رسائل: {user[2]}
⭐ VIP: {'نعم' if user[1] else 'لا'}"""
    )

# =========================
# MAIN HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)
    text = message.text

    db.create_user(user_id)
    db.reset_daily(user_id)

    mode = user_mode.get(user_id, "chat")

    # ================= MUSIC =================
    if mode == "music":

        bot.send_chat_action(message.chat.id, "upload_audio")

        prompt = f"""
اكتب أغنية عربية (8-12 سطر)
أسلوب راب أو شعبي
بدون مبالغة

الموضوع:
{text}
"""

        lyrics = chat([{"role": "user", "content": prompt}])

        # صوت
        tts = gTTS(lyrics, lang="ar")
        voice_file = f"{user_id}.mp3"
        tts.save(voice_file)

        # إرسال مباشر بدون pydub (حل مشاكل السيرفر)
        audio = open(voice_file, "rb")
        bot.send_audio(message.chat.id, audio, title="🎵 AI Song")
        audio.close()

        os.remove(voice_file)
        user_mode[user_id] = None
        return

    # ================= CHAT =================
    history = db.history(user_id)
    history.append({"role": "user", "content": text})

    response = chat(history)

    db.save(user_id, "user", text)
    db.save(user_id, "assistant", response)
    db.increase_count(user_id)

    bot.reply_to(message, response)

print("Bot Running...")
bot.polling()
