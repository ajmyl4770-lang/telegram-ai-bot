import os
import telebot
from groq import Groq
import config
import database  # استيراد قاعدة البيانات الصحيحة والمتوافقة مع مستودعك

# تهيئة البوت والذكاء الاصطناعي
bot_instance = telebot.TeleBot(config.BOT_TOKEN)
client = Groq(api_key=config.GROQ_API_KEY)

@bot_instance.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    database.create_user(user_id)
    bot_instance.reply_to(
        message, 
        "مرحباً بك في بوت الذكاء الاصطناعي لـ مركز بن علي! 🤖✨\nأنا جاهز لخدمتك والإجابة على استفساراتك الفنية."
    )

@bot_instance.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_id = str(message.chat.id)
    
    # فحص وتحديث القيود اليومية لضمان عدم تجاوز الـ 20 رسالة المجانية
    database.reset_daily(user_id)
    user_data = database.get_user(user_id)
    
    if not user_data:
        database.create_user(user_id)
        user_data = database.get_user(user_id)

    # التحقق من صلاحيات الـ VIP والحد اليومي
    if not database.is_vip(user_id) and user_data[2] >= database.FREE_LIMIT:
        bot_instance.reply_to(
            message, 
            "عذراً يا غالي، لقد استهلكت حدك المجاني اليومي (20 رسالة). لتفعيل الاستخدام اللامحدود تواصل مع إدارة المركز."
        )
        return

    # جلب ذاكرة المحادثة ودمج الرسالة الجديدة
    chat_history = database.get_history(user_id)
    chat_history.append({"role": "user", "content": message.text})

    try:
        # إرسال المحادثة إلى Groq
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=chat_history,
            temperature=0.7
        )
        
        response_text = completion.choices[0].message.content
        
        # حفظ الحوار وزيادة العداد في قاعدة البيانات
        database.save_chat(user_id, "user", message.text)
        database.save_chat(user_id, "assistant", response_text)
        database.increase_count(user_id)
        
        bot_instance.reply_to(message, response_text)

    except Exception as e:
        bot_instance.reply_to(message, "تأخرت استجابة السيرفر قليلاً، يرجى إعادة إرسال رسالتك.")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("...البوت يعمل الآن بأمان وتوافق تام")
    bot_instance.polling(none_stop=True)
