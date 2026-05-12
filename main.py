import telebot
from gtts import gTTS
import os

import config
import database as db
from ai import chat

bot = telebot.TeleBot(config.BOT_TOKEN)

user_mode = {}

bot.remove_webhook()
print("🤖 Bot is running...")


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك!")


@bot.message_handler(commands=['music'])
def music(message):
    user_mode[str(message.chat.id)] = "music"
    bot.reply_to(message, "🎵 اكتب فكرة الأغنية")


@bot.message_handler(func=lambda m: True)
def handle(message):
    uid = str(message.chat.id)

    if user_mode.get(uid) == "music":

        try:
            text = chat([{"role": "user", "content": message.text}])

            file = f"{uid}.mp3"
            gTTS(text=text, lang="ar").save(file)

            audio = open(file, "rb")
            bot.send_audio(message.chat.id, audio)

            audio.close()
            os.remove(file)

        except Exception as e:
            print(e)
            bot.reply_to(message, "⚠️ خطأ في إنشاء الصوت")

        user_mode[uid] = None
        return

    try:
        reply = chat([{"role": "user", "content": message.text}])
        bot.reply_to(message, reply)
    except:
        bot.reply_to(message, "⚠️ خطأ مؤقت")


bot.infinity_polling()
