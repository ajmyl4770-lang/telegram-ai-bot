from gtts import gTTS
import os
import telebot
import time
from telebot import types

import config
import database as db
from ai import chat

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}
last_msg = {}

# =========================
# لوحة
# =========================
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)

    m.row("💬 دردشة", "🖼️ صورة")
    m.row("🎵 أغنية", "📊 إحصائياتي")
    m.row("🧹 مسح الذاكرة")

    return m

# =========================
# start
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    db.create_user(uid)

    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك يا أبو جميل\n🤖 بوت ذكاء اصطناعي احترافي",
        reply_markup=menu()
    )

# =========================
# أزرار
# =========================
@bot.message_handler(func=lambda m: m.text == "💬 دردشة")
def chat_mode(m):
    user_mode[str(m.chat.id)] = "chat"
    bot.reply_to(m, "💬 أرسل رسالتك")

@bot.message_handler(func=lambda m: m.text == "🖼️ صورة")
def img_mode(m):
    user_mode[str(m.chat.id)] = "image"
    bot.reply_to(m, "🖼️ أرسل وصف الصورة")

@bot.message_handler(func=lambda m: m.text == "🎵 أغنية")
def music_mode(m):
    user_mode[str(m.chat.id)] = "music"
    bot.reply_to(m, "🎵 أرسل فكرة الأغنية")

@bot.message_handler(func=lambda m: m.text == "📊 إحصائياتي")
def stats(m):
    u = db.get_user(str(m.chat.id))

    if not u:
        bot.reply_to(m, "لا يوجد بيانات")
        return

    bot.reply_to(m,
        f"📊 الإحصائيات:\n\n💬 رسائل: {u[2]}\n⭐ VIP: {'نعم' if u[1] else 'لا'}"
    )

@bot.message_handler(func=lambda m: m.text == "🧹 مسح الذاكرة")
def clear(m):
    uid = str(m.chat.id)

    db.cur.execute("DELETE FROM messages WHERE user_id=?", (uid,))
    db.conn.commit()

    bot.reply_to(m, "🧹 تم المسح")

# =========================
# الذكاء الاصطناعي
# =========================
@bot.message_handler(func=lambda m: True)
def handle(m):

    uid = str(m.chat.id)

    try:
        db.create_user(uid)
        db.reset_daily(uid)

        user = db.get_user(uid)

        if not user:
            user = (uid, 0, 0, 0)

        if not db.is_vip(uid) and user[2] >= config.FREE_LIMIT:
            bot.reply_to(m, "❌ انتهى الحد اليومي")
            return

        mode = user_mode.get(uid, "chat")

        # =========================
        # أغاني
        # =========================
        if mode == "music":

    bot.send_chat_action(message.chat.id, "upload_audio")

    prompt = f"""
اكتب أغنية عربية قصيرة بأسلوب راب أو شعبي.

- 8 إلى 12 سطر
- كلمات قوية
- بدون تكرار

الموضوع:
{message.text}
"""

    response = chat([{"role": "user", "content": prompt}])

    # =========================
    # تحويل النص إلى صوت
    # =========================
    try:
        tts = gTTS(text=response, lang="ar")
        file_path = f"{uid}.mp3"
        tts.save(file_path)

        audio = open(file_path, "rb")

        bot.send_audio(
            message.chat.id,
            audio,
            title="🎵 أغنيتك",
            caption="🤖 تم إنشاؤها بواسطة البوت"
        )

        audio.close()
        os.remove(file_path)

    except Exception as e:
        print("AUDIO ERROR:", e)
        bot.reply_to(message, response)

    user_mode[uid] = None
    return

        # =========================
        # صورة (وصف فقط)
        # =========================
        if mode == "image":
            bot.reply_to(m, f"🖼️ وصف الصورة:\n{m.text}")
            user_mode[uid] = None
            return

        # =========================
        # دردشة
        # =========================
        hist = db.history(uid)
        hist.append({"role": "user", "content": m.text})

        bot.send_chat_action(m.chat.id, "typing")

        res = chat(hist)

        db.save(uid, "user", m.text)
        db.save(uid, "assistant", res)
        db.increase_count(uid)

        bot.reply_to(m, res)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(m, "⚠️ خطأ مؤقت")

print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
