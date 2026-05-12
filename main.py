import os
import telebot
from groq import Groq
import bot  # ملف إدارة قاعدة البيانات والمستخدمين
import config # لاستخدام الإعدادات من ملف config.py

# جلب الإعدادات
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
bot_instance = telebot.TeleBot(os.getenv("BOT_TOKEN"))
MODEL = "llama-3.3-70b-versatile"

@bot_instance.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    bot.create_user(user_id)
    bot_instance.reply_to(message, "مرحباً بك! أنا بوت الذكاء الاصطناعي الخاص بمركز بن علي. كيف يمكنني مساعدتك اليوم؟")

@bot_instance.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_id = str(message.chat.id)
    
    # تحديث عداد الاستخدام اليومي
    bot.reset_daily(user_id)
    user_data = bot.get_user(user_id)
    
    # التحقق من حد الاستخدام (20 رسالة مجانية)
    if not bot.is_vip(user_id) and user_data[2] >= bot.FREE_LIMIT:
        bot_instance.reply_to(message, "عذراً، لقد وصلت للحد الأقصى للرسائل المجانية اليوم (20 رسالة).")
        return

    # جلب سجل المحادثة من قاعدة البيانات
    messages_history = bot.history(user_id)
    messages_history.append({"role": "user", "content": message.text})

    try:
        # إرسال الطلب لـ Groq
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages_history,
            temperature=0.7
        )
        
        response_text = completion.choices[0].message.content
        
        # حفظ الرسالة والرد في قاعدة البيانات
        bot.save(user_id, "user", message.text)
        bot.save(user_id, "assistant", response_text)
        bot.increase_count(user_id)
        
        bot_instance.reply_to(message, response_text)

    except Exception as e:
        bot_instance.reply_to(message, "حدث خطأ فني، يرجى المحاولة لاحقاً.")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("البوت يعمل الآن بأمان...")
    bot_instance.polling()
