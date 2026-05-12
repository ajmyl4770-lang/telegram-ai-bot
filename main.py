import os
import telebot
import config
import database as db
from ai import chat

bot = telebot.TeleBot(config.BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)

    db.create_user(user_id)

    bot.send_message(
        message.chat.id,
        "👋 مرحباً بك!\nأنا بوت ذكاء اصطناعي متطور.\nارسل أي سؤال وسأساعدك."
    )


@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    db.create_user(user_id)
    db.reset_daily(user_id)

    user = db.get_user(user_id)

    if not user:
        user = (user_id, 0, 0, 0)

    # حد الاستخدام
    if not db.is_vip(user_id) and user[1] >= config.FREE_LIMIT:
        bot.reply_to(message, "❌ وصلت للحد اليومي (20 رسالة).")
        return

    history = db.history(user_id)
    history.append({"role": "user", "content": message.text})

    response = chat(history)

    db.save(user_id, "user", message.text)
    db.save(user_id, "assistant", response)
    db.increase_count(user_id)

    bot.reply_to(message, response)


print("🤖 Bot is running...")
bot.polling()
