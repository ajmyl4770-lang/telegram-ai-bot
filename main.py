import telebot
import time
from telebot import types
from gtts import gTTS
import os

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
def start(m):
    uid = str(m.chat.id)

    db.create_user(uid)

    bot.send_message(
        m.chat.id,
        "👋 أهلاً بك يا أبو جميل\n🤖 نسخة احترافية من البوت",
        reply_markup=menu()
    )


# =========================
# الأزرار
# =========================
@bot.message_handler(func=lambda m: m.text == "💬 دردشة")
def chat_mode(m):
    user_mode[str(m.chat.id)] = "chat"
    bot.reply_to(m, "💬 اكتب رسالتك")


@bot.message_handler(func=lambda m: m.text == "🖼️ صورة")
def img_mode(m):
    user_mode[str(m.chat.id)] = "image"
    bot.reply_to(m, "🖼️ اكتب وصف الصورة")


@bot.message_handler(func=lambda m: m.text == "🎵 أغنية")
def music_mode(m):
    user_mode[str(m.chat.id)] = "music"
    bot.reply_to(m, "🎵 اكتب فكرة الأغنية")


@bot.message_handler(func=lambda m: m.text == "📊 إحصائياتي")
def stats(m):
    u = db.get_user(str(m.chat.id))

    if not u:
        bot.reply_to(m, "لا يوجد بيانات")
        return

    bot.reply_to(m,
        f"📊 الرسائل: {u[2]}\n⭐ VIP: {'نعم' if u[1] else 'لا'}"
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
        # أغاني + صوت
        # =========================
        if mode == "music":

            bot.send_chat_action(m.chat.id, "upload_audio")

            prompt = f"""
اكتب أغنية عربية قوية (راب/شعبي)
8-12 سطر
بدون مبالغة

الموضوع:
{m.text}
"""

            text = chat([{"role": "user", "content": prompt}])

            try:
                tts = gTTS(text=text, lang="ar")
                file = f"{uid}.mp3"
                tts.save(file)

                audio = open(file, "rb")

                bot.send_audio(m.chat.id, audio)

                audio.close()
                os.remove(file)

            except:
                bot.reply_to(m, text)

            user_mode[uid] = None
            return


        # =========================
        # صورة (وصف)
        # =========================
        if mode == "image":
            bot.reply_to(m, f"🖼️ تم توليد وصف:\n{m.text}")
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


print("🤖 Production Bot Running...")
bot.infinity_polling(skip_pending=True)
