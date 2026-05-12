@bot_instance.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)

    try:
        db.create_user(user_id)
        db.reset_daily(user_id)

        user = db.get_user(user_id)
        if not user:
            user = (user_id, 0, 0, 0)

        if not db.is_vip(user_id) and user[1] >= db.FREE_LIMIT:
            bot_instance.reply_to(message, "❌ وصلت الحد اليومي.")
            return

        messages_history = db.history(user_id)
        messages_history.append({"role": "user", "content": message.text})

        response = chat(messages_history)

        db.save(user_id, "user", message.text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot_instance.reply_to(message, response)

    except Exception as e:
        print("ERROR:", e)
        bot_instance.reply_to(message, "⚠️ حصل خطأ مؤقت، حاول مرة ثانية.")
