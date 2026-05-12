import telebot
import os
from gtts import gTTS
from pydub import AudioSegment

import config
import database as db
from ai import chat

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}


# =========================
# Start
# =========================
@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.chat.id)

    db.create_user(uid)

    bot.send_message(
        m.chat.id,
        "👋 أهلاً بك يا أبو جميل\n🤖 بوت AI احترافي",
    )


# =========================
# Clear
# =========================
@bot.message_handler(commands=['clear'])
def clear(m):
    uid = str(m.chat.id)

    db.cur.execute("DELETE FROM messages WHERE user_id=?", (uid,))
    db.conn.commit()

    bot.reply_to(m, "🧹 تم مسح الذاكرة")


# =========================
# Music Mode
# =========================
@bot.message_handler(func=lambda m: True)
def handle(m):

    uid = str(m.chat.id)

    db.create_user(uid)
    db.reset_daily(uid)

    user = db.get_user(uid)

    if not user:
        user = (uid, 0, 0, 0)

    if not db.is_vip(uid) and user[2] >= config.FREE_LIMIT:
        bot.reply_to(m, "❌ انتهى الحد اليومي")
        return

    mode = user_mode.get(uid, "chat")

    # 🎵 MUSIC
    if mode == "music":

        bot.send_chat_action(m.chat.id, "upload_audio")

        prompt = f"""
اكتب أغنية راب عربية 8-12 سطر
بدون مبالغة

الموضوع:
{m.text}
"""

        try:
            lyrics = chat([{"role": "user", "content": prompt}])

            # voice
            tts = gTTS(text=lyrics, lang="ar")
            voice_file = f"{uid}_voice.mp3"
            tts.save(voice_file)

            # beat
            beat = AudioSegment.from_file("beat.mp3")
            voice = AudioSegment.from_file(voice_file)

            voice = voice - 3

            final = beat.overlay(voice)

            output = f"{uid}_song.mp3"
            final.export(output, format="mp3")

            audio = open(output, "rb")

            bot.send_audio(
                m.chat.id,
                audio,
                title="🎵 AI Song"
            )

            audio.close()

            os.remove(voice_file)
            os.remove(output)

        except Exception as e:
            print(e)
            bot.reply_to(m, "⚠️ خطأ في الأغنية")

        user_mode[uid] = None
        return


    # 💬 CHAT
    history = db.history(uid)
    history.append({"role": "user", "content": m.text})

    bot.send_chat_action(m.chat.id, "typing")

    res = chat(history)

    db.save(uid, "user", m.text)
    db.save(uid, "assistant", res)
    db.increase_count(uid)

    bot.reply_to(m, res)


print("🤖 Bot Running...")
bot.infinity_polling(skip_pending=True)
