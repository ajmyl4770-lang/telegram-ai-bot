import os
import telebot
import config
import database as db
from ai import chat
from gtts import gTTS

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}
user_style = {}


# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    db.create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك يا أبو جميل\n\n"
        "🤖 بوت احترافي للأغاني والذكاء الاصطناعي\n\n"
        "🎵 /music خليجي\n"
        "🎵 /music مصري\n"
        "🎵 /music يمني\n"
        "🎵 /music شيلات\n"
        "📊 /stats\n"
        "🧹 /clear"
    )


# =========================
# MUSIC SELECT STYLE
# =========================
@bot.message_handler(commands=['music'])
def music(message):
    user_id = str(message.chat.id)

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "اكتب: /music خليجي أو مصري أو يمني أو شيلات")
        return

    style = parts[1].lower()

    if style not in ["خليجي", "مصري", "يمني", "شيلات"]:
        bot.reply_to(message, "اختر: خليجي / مصري / يمني / شيلات")
        return

    user_mode[user_id] = "music"
    user_style[user_id] = style

    bot.reply_to(message, f"🎵 اكتب فكرة الأغنية ({style}) الآن")


# =========================
# MAIN HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    try:
        db.create_user(user_id)
        db.reset_daily(user_id)

        mode = user_mode.get(user_id, "chat")

        # =========================
        # MUSIC MODE
        # =========================
        if mode == "music":

            style = user_style.get(user_id, "خليجي")

            bot.send_chat_action(message.chat.id, "upload_audio")

            prompt = f"""
اكتب أغنية عربية بأسلوب {style}

- 10 إلى 14 سطر
- بدون تكرار
- كلمات قوية وموسيقى راب أو شعبية
- مناسبة لأسلوب {style}

الموضوع:
{message.text}
"""

            lyrics = chat([{"role": "user", "content": prompt}])

            # ===== صوت =====
            voice_file = f"{user_id}_voice.mp3"
            tts = gTTS(text=lyrics, lang="ar")
            tts.save(voice_file)

            # ===== اختيار Beat =====
            beat_map = {
                "خليجي": "beats/gulf.mp3",
                "مصري": "beats/egypt.mp3",
                "يمني": "beats/yemen.mp3",
                "شيلات": "beats/shilat.mp3"
            }

            beat_file = beat_map.get(style, "beats/gulf.mp3")

            output_file = f"{user_id}_final.mp3"

            # ===== دمج احترافي FFmpeg =====
            os.system(f"""
ffmpeg -y -i {beat_file} -i {voice_file} -filter_complex \
"[1:a]volume=1.2[a1];[0:a][a1]amix=inputs=2:duration=longest" \
-b:a 192k {output_file}
""")

            # ===== إرسال =====
            with open(output_file, "rb") as audio:
                bot.send_audio(
                    message.chat.id,
                    audio,
                    title=f"🎵 AI Song - {style}",
                    caption="🔥 أغنية احترافية بالذكاء الاصطناعي"
                )

            # تنظيف
            os.remove(voice_file)
            os.remove(output_file)

            user_mode[user_id] = None
            user_style[user_id] = None
            return

        # =========================
        # CHAT MODE
        # =========================
        history = db.history(user_id)
        history.append({"role": "user", "content": message.text})

        response = chat(history)

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)

        bot.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "⚠️ حصل خطأ")


print("🤖 Bot is running...")
bot.infinity_polling()
