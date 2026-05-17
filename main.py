import os
import telebot
from groq import Groq
import config
import database  # استيراد ملف قاعدة البيانات المتوافق

# تهيئة الخدمات باستخدام المتغيرات الآمنة
bot_instance = telebot.TeleBot(config.BOT_TOKEN)
client = Groq(api_key=config.GROQ_API_KEY)

@bot_instance.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    database.create_user(user_id)
    bot_instance.reply_to(
        message, 
        "مرحباً بك في بوت الذكاء الاصطناعي لـ مركز بن علي! 🤖✨\nأنا جاهز لخدمتك ومساعدتك."
    )

@bot_instance.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_id = str(message.chat.id)
    
    # تحديث القيود اليومية (20 رسالة مجانية)
    database.reset_daily(user_id)
    user_data = database.get_user(user_id)
    
    if not user_data:
        database.create_user(user_id)
        user_data = database.get_user(user_id)

    # التحقق من صلاحية الاستخدام للمخدم
    if not database.is_vip(user_id) and user_data[2] >= database.FREE_LIMIT:
        bot_instance.reply_to(
            message, 
            "عذراً يا غالي، لقد استهلكت حدك المجاني اليومي (20 رسالة)."
        )
        return

    # جلب الذاكرة وإرسالها إلى Groq لتذكر سياق الحوار
    chat_history = database.get_history(user_id)
    chat_history.append({"role": "user", "content": message.text})

    try:
        # الاتصال بـ Groq
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=chat_history,
            temperature=0.7
        )
        
        response_text = completion.choices[0].message.content
        
        # حفظ الحوار وزيادة العداد
        database.save_chat(user_id, "user", message.text)
        database.save_chat(user_id, "assistant", response_text)
        database.increase_count(user_id)
        
        bot_instance.reply_to(message, response_text)

    except Exception as e:
        # تعديل لعرض تفاصيل الخطأ في السجلات البرمجية للمنصة لسهولة الفحص
        error_message = str(e)
        bot_instance.reply_to(message, "حدث ضغط مؤقت على السيرفر، يرجى المحاولة مرة أخرى.")
        print(f"GROQ API ERROR: {error_message}")

from flask import Flask, request

app = Flask(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

@app.route(f"/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot_instance.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    print("🚀 البوت يعمل بنظام Webhook")

    bot_instance.remove_webhook()
    bot_instance.set_webhook(
        url=f"{WEBHOOK_URL}/{config.BOT_TOKEN}"
    )

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
